"""Native layer 233 equivalents of the existing widget HTTPS methods."""
from pyrogram import enums, raw, types, utils
from pyrogram.methods.messages.inline_session import invoke_inline


def _entities(values):
    result = []
    for value in values:
        if not isinstance(value, dict):
            result.append(value)
            continue
        value = dict(value)
        kind = value.pop("type")
        if kind == "expandable_blockquote":
            kind = "blockquote"
            value["expandable"] = True
        if isinstance(value.get("user"), dict):
            value["user"] = types.User(id=value["user"]["id"])
        result.append(types.MessageEntity(type=enums.MessageEntityType[kind.upper()], **value))
    return result


def _button(values, cls):
    values = dict(values)
    nested = {"login_url": types.LoginUrl, "web_app": types.WebAppInfo,
              "copy_text": types.CopyTextButton,
              "switch_inline_query_chosen_chat": types.SwitchInlineQueryChosenChat,
              "request_poll": types.KeyboardButtonPollType,
              "request_users": types.KeyboardButtonRequestUsers,
              "request_chat": types.KeyboardButtonRequestChat,
              "request_managed_bot": types.KeyboardButtonRequestManagedBot}
    for key, child in nested.items():
        if isinstance(values.get(key), dict):
            values[key] = child(**values[key])
    if isinstance(values.get("style"), str):
        values["style"] = enums.ButtonStyle[values["style"].upper()]
    if "callback_game" in values:
        values["callback_game"] = types.CallbackGame()
    return cls(**values)


async def caption(client, payload):
    text = payload.get("caption") or ""
    if payload.get("caption_entities") is not None:
        entities = _entities(payload["caption_entities"])
        for entity in entities:
            entity._client = client
        return {"message": text, "entities": [await e.write() for e in entities] or None}
    mode = payload.get("parse_mode")
    if mode is None or mode == enums.ParseMode.DISABLED:
        return {"message": text, "entities": None}
    if isinstance(mode, str):
        mode = {"html": enums.ParseMode.HTML, "markdown": enums.ParseMode.MARKDOWN,
                "markdownv2": enums.ParseMode.MARKDOWN}.get(mode.lower(), mode)
    return await utils.parse_text_entities(client, text, mode, None)


async def markup(client, value):
    if value is None:
        return None
    if isinstance(value, dict):
        value = dict(value)
        if "inline_keyboard" in value:
            rows = []
            for row in value["inline_keyboard"]:
                buttons = []
                for item in row:
                    buttons.append(_button(item, types.InlineKeyboardButton))
                rows.append(buttons)
            value = types.InlineKeyboardMarkup(rows)
        elif "keyboard" in value:
            value["keyboard"] = [[_button(b, types.KeyboardButton) if isinstance(b, dict) else b
                                  for b in row] for row in value["keyboard"]]
            if "input_field_placeholder" in value:
                value["placeholder"] = value.pop("input_field_placeholder")
            value = types.ReplyKeyboardMarkup(**value)
        elif value.pop("remove_keyboard", False):
            value = types.ReplyKeyboardRemove(**value)
        elif value.pop("force_reply", False):
            if "input_field_placeholder" in value:
                value["placeholder"] = value.pop("input_field_placeholder")
            value = types.ForceReply(**value)
        else:
            raise ValueError("Unknown widget reply_markup")
    return await value.write(client)


async def widget_request(client, method, payload):
    if method in ("sendWidget", "sendSharedWidget"):
        if method == "sendWidget":
            media = raw.types.InputMediaWidget(
                html=payload["html"], width=payload.get("width") or 0,
                height=payload.get("height") or 0,
                allow_queries=payload.get("allow_queries"), shared_widget=payload.get("is_shared"),
                chat_data=payload.get("chat_data"), public_data=payload.get("public_data")
            )
        else:
            media = raw.types.InputMediaWidgetId(
                widget_id=int(payload["widget_id"]), chat_data=payload.get("chat_data")
            )
        reply = payload.get("reply_parameters")
        if isinstance(reply, dict):
            reply = dict(reply)
            reply.pop("allow_sending_without_reply", None)
            if reply.get("quote_entities") is not None:
                reply["quote_entities"] = _entities(reply["quote_entities"])
            reply = types.ReplyParameters(**reply)
        result = await client.invoke(raw.functions.messages.SendMedia(
            peer=await client.resolve_peer(payload["chat_id"]), media=media,
            random_id=client.rnd_id(),
            reply_to=await utils.get_reply_to(client, reply, payload.get("message_thread_id")),
            reply_markup=await markup(client, payload.get("reply_markup")),
            silent=payload.get("disable_notification"), noforwards=payload.get("protect_content"),
            invert_media=payload.get("show_caption_above_media"),
            allow_paid_floodskip=payload.get("allow_paid_broadcast"),
            effect=int(payload["message_effect_id"]) if payload.get("message_effect_id") else None,
            **await caption(client, payload)
        ))
        for update in result.updates:
            if isinstance(update, (raw.types.UpdateNewMessage, raw.types.UpdateNewChannelMessage)):
                return await types.Message._parse(
                    client, update.message, {u.id: u for u in result.users},
                    {c.id: c for c in result.chats}
                )
        raise RuntimeError("Telegram returned no message for the widget send")
    if method == "answerWidgetQuery":
        return await client.invoke(raw.functions.messages.SetBotWidgetQueryAnswer(
            query_id=int(payload["widget_query_id"]), result=payload.get("data")
        ))
    if method == "editSharedWidgetData":
        return await client.invoke(raw.functions.messages.EditWidgetData(
            widget_id=int(payload["widget_id"]), public_data=payload["public_data"],
            cache_time=payload.get("cache_time")
        ))
    if method == "editMessageWidgetData":
        values = {name: payload[name] for name in ("chat_data", "public_data") if name in payload}
        if "inline_message_id" in payload:
            inline_id = utils.unpack_inline_message_id(payload["inline_message_id"])
            return await invoke_inline(client, inline_id.dc_id,
                raw.functions.messages.EditInlineBotMessageWidgetData(id=inline_id, **values))
        await client.invoke(raw.functions.messages.EditMessageWidgetData(
            peer=await client.resolve_peer(payload["chat_id"]), id=payload["message_id"], **values
        ))
        return True
    raise ValueError(f"Unsupported native widget method: {method}")
