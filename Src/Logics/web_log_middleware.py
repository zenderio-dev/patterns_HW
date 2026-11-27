from Src.Core.event_publisher import events


class web_log_middleware:
    """Публикует метод, путь и статус ответа веб-запроса."""

    def __init__(self, app):
        """Запомнить следующий обработчик запроса."""
        self.__app = app

    async def __call__(self, scope, receive, send):
        """Записать статус после отправки заголовков ответа."""
        if scope["type"] != "http":
            await self.__app(scope, receive, send)
            return

        async def send_response(message):
            """Передать ответ и опубликовать его HTTP-статус."""
            await send(message)
            if message["type"] == "http.response.start":
                status = message["status"]
                level = "ERROR" if status >= 400 else "INFO"
                events.publish("web", level, f"{scope['method']} {scope['path']} {status}")

        await self.__app(scope, receive, send_response)
