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
            TextSendMessage(text='Display name : ' + profile.display_name),
            TextSendMessage(text='Status message : ' + profile.status_message)
        ]
    }

def follow_messages():
    messages = []
    messages.append(
        TextSendMessage(text='follow Event')
    )
    return messages
    
def other_messages(text, user):
    messages = []
    messages.append(
        TextSendMessage(text=text)
    )
    return messages