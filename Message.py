from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton
)

def profile_messages(text, user, profile):
    return {
        "error":[TextSendMessage(text='プロフィール情報を取得できませんでした。')],
        'ok':[
            TextSendMessage(text='表示名 : ' + profile.display_name),
            TextSendMessage(text='状態コメント : ' + profile.status_message)
        ]
    }

def pre_save_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text='あなたのアイデアを入力してください！')
    )
    return messages

def pre_save_iken(text, user):
    messages = []
    messages.append(
        TextSendMessage(
            text='忌憚ないご意見をお願いします。'
        )
    )
    return messages

def thanks_idea_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text='アイデアを入力してくれてありがとう！')
    )
    messages.append(
        TemplateSendMessage(
            alt_text='表示できない状態です。スマートフォンから見てください！',
            template=ButtonsTemplate(
                title='カテゴリー', text='カテゴリーを選んでください。\n自由記述でも受け付けているよ！',
                actions=[
                    MessageAction(label='テクノロジー', text='テクノロジー'),
                    MessageAction(label='起業', text='起業'),
                    MessageAction(label='文系', text='文系'),
                    MessageAction(label='その他', text='その他')
                ]
            )
        )
    )
    return messages

def thanks_cat_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text='カテゴリーを登録してくれてありがとうございます！\nカテゴリーとアイデアの結びつきは後の参考とさせていただきます。')
    )
    return messages

def thanks_iken_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text='ご意見くださりありがとうございます。この意見は活かせる範囲で活かします。')
    )
    return messages

def random_idea_reply_messages(idea, user):
    messages = []
    messages.append(
        TextSendMessage(text='こんなアイデアがあるよ！\n-----\n' + idea + '\n-----')
    )
    messages.append(
        TemplateSendMessage(
            alt_text='表示できない状態です。スマートフォンから見てください！',
            template=ConfirmTemplate(
                text='いいねしますか？',
                actions=[
                    MessageAction(label='いいね！', text='いいね！'),
                    MessageAction(label='評価しない', text='評価しない')
                ]
            )
        )
   )
    return messages

def lets_idea_messages():
    messages = []
    messages.append(
        TextSendMessage(text='Let\'s tell me your special idea!')
    )
    return messages

def thanks_idea_fav():
    messages = []
    messages.append(
        TextSendMessage(text='いいねしてくれてありがとう！')
    )
    return messages

def thanks_idea_no_fav():
    messages = []
    messages.append(
        TextSendMessage(text='また評価してね～！')
    )
    return messages

def follow_messages():
    messages = []
    messages.append(
        TextSendMessage(text='フォローしてくれてありがとう！\n「保存する」と入力して、アイデアを入力してね。\n「アイデアを見る」と入力するとランダムで誰かのアイデアが一つ見れるよ')
    )
    return messages

def other_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text='使い方は簡単！\n「保存する」でアイデアを保存できるよ。「アイデアを見る」で誰かのアイデアをランダムで一つ見ることができるよ。')
    )
    return messages
