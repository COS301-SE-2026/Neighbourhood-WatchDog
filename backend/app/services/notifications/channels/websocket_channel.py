from app.services.notifications.channel import NotificationChannel

class WebSocketChannel(NotificationChannel):
    async def send():
        pass #TODO: implement. This one aint adding to the queue this one sends straight via WebSocket