# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
from argparse import ArgumentParser

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)

from linebot.models import (
    MessageEvent, SourceUser, TextMessage, UnfollowEvent, FollowEvent
)

import Message as line_bot_reply_message

from flask import Flask, render_template, request, redirect, url_for, abort, session, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
import flask_admin
from flask_admin import BaseView, expose
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from datetime import datetime
import random
import time
import json

import config

app = Flask(__name__)
app.config.from_pyfile('config.py')
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
db_uri = 'sqlite:///{}'.format(db_path)
#app.config['SQLALCHEMY_DATABASE_URI'] = db_uri #テスト環境用
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'] #本番環境用
db = SQLAlchemy(app)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    '''ユーザの情報を蓄えるデータベース'''

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    #初期情報:フォローした瞬間に生成される情報
    line_user_id = db.Column(db.String(255), unique=True)
    user_name = db.Column(db.String(80))
    connect_date = db.Column(db.DateTime)
    profile = db.Column(db.String(255))

    #ユーザの状態：なんかわからんけどメッセージ入力を受け付けるときには数字を変えるとかしたいね。
    # 0 or None : no state
    # 1 : waiting for new idea
    # 2 : waiting for eavluating
    # 3 : アイデアを述べた後、カテゴリーを記述する前
    # 4 : 意見を受け付ける状態。
    state = db.Column(db.Integer)


    #このユーザが最後に見たアイデアのid
    #これ本当は配列的な持ち方をできるようにすべきかな。
    last_idea_id = db.Column(db.Integer)

    #ここ管理者だけ
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('user', lazy='dynamic'))

class Message(db.Model):
    __tablename__='message'

    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)

    # 0 or None : plain message
    # 1 : idea message
    # 2 : no active idea
    # 3 : 要望
    comment_type = db.Column(db.Integer)

    # how many times the idea has look
    count_look = db.Column(db.Integer)

    # いいねの数
    count_good = db.Column(db.Integer)

    #カテゴリー
    category = db.Column(db.String(255))

    # the state of user's activities
    user_state = db.Column(db.Integer)

    date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class MyRoleView(sqla.ModelView):
    '''
    役職管理画面だが、今回はこれを表示しない
    '''
    can_delete = False
    can_edit = False
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('superuser'):
            return True
        return False
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next=request.url))

class MyUserView(sqla.ModelView):
    '''
    ユーザ管理画面だが、今回はこれを表示せず自前で作成する
    '''
    can_delete = True
    can_edit = False

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('superuser'):
            return True
        return False

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next=request.url))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

admin = flask_admin.Admin(
    app,
    'WOWOWOW',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

admin.add_view(MyRoleView(Role, db.session))
admin.add_view(MyUserView(User, db.session))

@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

@app.route('/inactivecom', methods=['POST'])
def inactivecom():
    num = request.form['num']
    print(num)
    num = int(num)
    ms = db.session.query(Message).filter(Message.id == num).all()
    for m in ms:
        m.comment_type = 2
    db.session.flush()
    db.session.commit()
    #return 'Hello World'
    return redirect(url_for('show_messages'))

@app.route('/reactive', methods=['POST'])
def reactive():
    num = request.form['num']
    activetype = request.form['activetype']
    num = int(num)
    activetype = int(activetype)
    ms = db.session.query(Message).filter(Message.id == num).all()
    for m in ms:
        m.comment_type = activetype
    db.session.flush()
    db.session.commit()
    #return 'Hello World'
    return redirect(url_for('show_messages'))

@app.route('/messages', methods=['GET'])
def show_messages():
    ms = db.session.query(Message).all().order_by(desc(Message.date))
    render_data = []
    for m in ms:
        is_active = True
        if m.comment_type == 2:
            is_active = False

        if m.date:
            date = m.date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = 'not set'
        render_data.append({
            'id':m.id,
            'comment':m.comment,
            'type':m.comment_type,
            'date':date,
            'count':m.count_look,
            'good':m.count_good,
            'cat':m.category,
            'is_active':is_active
        })
        print(date)
        #todo: output "count_look"
    return render_template('messages.html', render_data = render_data)

@app.route('/messages/<mtype>', methods=['GET'])
def show_messages_wtype(mtype=None):
    mnum = 0
    if mtype == 'idea':
        mnum = 1
    elif mtype == 'iken':
        mnum = 3
    ms = db.session.query(Message).filter(Message.comment_type == mnum).all()
    render_data = []
    for m in ms:
        if m.date:
            date = m.date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = 'not set'
        render_data.append({
            'id':m.id,
            'comment':m.comment,
            'type':m.comment_type,
            'date':date,
            'count':m.count_look,
            'good':m.count_good,
            'cat':m.category
        })
        print(date)
        #todo: output "count_look"
    return render_template('messages.html', render_data = render_data)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    line_user_id = event.source.user_id
    user = User.query.filter(User.line_user_id == line_user_id).first()

    comment_type = 0
    now = datetime.now()

    if text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, line_bot_reply_message.profile_messages(text, user, profile)["ok"]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                line_bot_reply_message.profile_messages(text, user, profile)['error']
            )
    elif text == 'save' or text == '保存する':
        user.state = 1
        '''
        アイデアを保存するコマンドを実行します。
        '''
        db.session.flush()
        db.session.commit()
        line_bot_api.reply_message(event.reply_token, line_bot_reply_message.pre_save_messages(text, user))
    elif text == 'want' or text == '要望を送る':
        user.state = 4
        # 要望を受け付ける
        db.session.flush()
        db.session.commit()

        line_bot_api.reply_message(event.reply_token, line_bot_reply_message.pre_save_iken(text, user))

    elif text == 'look' or text == 'アイデアを見る':
        user.state = 2
        # ランダムにidea一つ取得しています。これもっと高速化しましょう。
        # TODO: 一つ目のfilterはnotに変えて使ってください。
        all_messages = Message.query.filter(Message.comment_type == 1).all()
        rc = random.choice(all_messages)
        if not rc.count_look is None:
            rc.count_look = rc.count_look + 1
        else:
            rc.count_look = 0
        #print(rc.comment)
        messages = line_bot_reply_message.random_idea_reply_messages(rc.comment, user)
        user.last_idea_id = rc.id

        db.session.flush()
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token, messages
        )
    else:
        messages = line_bot_reply_message.other_messages(text, user) #デフォルトのメッセージを設定
        if user.state == 1: #アイデア待ちの段階
            comment_type = 1
            messages = line_bot_reply_message.thanks_idea_messages(text, user)

            user.state = 3
        elif user.state == 2:
            # 評価待ちの状態、ここからのメッセージは評価、コメントになる。今はgoodしかない

            user.state = 0

            messages = line_bot_reply_message.lets_idea_messages()
            _m = Message.query.filter(Message.id == user.last_idea_id).first_or_404()
            if (text == 'いいね！' or text == 'いいね') and _m:
                messages = line_bot_reply_message.thanks_idea_fav()
                if not _m.count_good is None:
                    _m.count_good = _m.count_good + 1
                else:
                    _m.count_good = 0
                print(_m.count_good)
            elif text == '評価しない' and _m:
                messages = line_bot_reply_message.thanks_idea_no_fav()

        elif user.state == 3:
            #カテゴリー受付状態。

            user.state = 0
            messages = line_bot_reply_message.thanks_cat_messages(text, user)

            #自分の最後のアイデアメッセージを取得する
            last_my_idea = Message.query.filter(Message.user_id == user.id).order_by(Message.id.desc()).first_or_404()
            if last_my_idea:
                last_my_idea.category = text
        elif user.state == 4:
            # 意見受け付けた後
            messages = line_bot_reply_message.thanks_iken_messages(text, user)
            comment_type = 3
            user.state = 0

        # user.state = 0
        line_bot_api.reply_message(
            event.reply_token,
            messages
        )
        db.session.flush()
        db.session.commit()
    m = Message(
        comment=text,
        comment_type=comment_type,
        user_id=user.id,
        date=datetime.fromtimestamp(int(event.timestamp/1000)),
        count_good = 0,
        count_look = 0
    )
    db.session.add(m)
    #db.session.flush()
    db.session.commit()

@handler.add(FollowEvent)
def handle_follow(event):
    source_str = 'abcdefghijklmnopqrstuvwxyz0123456789'
    random_url =  "".join([random.choice(source_str) for x in range(20)])

    line_user_id = event.source.user_id
    profile = line_bot_api.get_profile(line_user_id)
    user_name = profile.display_name
    connect_time = datetime.fromtimestamp(int(event.timestamp/1000))

    user_datastore.create_user(
        line_user_id=line_user_id,
        user_name=user_name,
        connect_date=connect_time,
        password=encrypt_password("".join([random.choice(source_str) for x in range(35)])),
        roles=[Role(name='user'), ],
        profile=profile.display_name,
        state = 0,
        last_idea_id = -1
    )

    db.session.commit()
    line_bot_api.reply_message(
        event.reply_token,
        line_bot_reply_message.follow_messages()
    )

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    #line_user_id = event.source.user_id
    #user = User.query.filter(User.line_user_id == line_user_id).first()
    users = db.session.query(User).filter(User.line_user_id == event.source.user_id)
    for user in users:
        print(user.user_name)
        db.session.delete(user)
        db.session.commit()
    app.logger.info("Got Unfollow event")


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)
