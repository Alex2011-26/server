import asyncio
import json
import random
import string
import websockets

rooms = {}
socket_to_room = {}
all_clients = set()

def generate_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

async def handler(websocket):
    all_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get('action')

            if action == 'create_room':
                room_id = generate_room_id()
                rooms[room_id] = {websocket}
                socket_to_room[websocket] = room_id
                await websocket.send(json.dumps({'type': 'room_created', 'room_id': room_id}))
                for client in all_clients:
                    await client.send(json.dumps({'type': 'room_added', 'room_id': room_id, 'players': 1}))

            elif action == 'join_room':
                room_id = data['room_id']
                if room_id in rooms and len(rooms[room_id]) < 2:
                    rooms[room_id].add(websocket)
                    socket_to_room[websocket] = room_id
                    for ws in rooms[room_id]:
                        await ws.send(json.dumps({'type': 'player_joined', 'count': len(rooms[room_id])}))
                else:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Room not found or full'}))

            elif action == 'message':
                room_id = socket_to_room.get(websocket)
                if room_id:
                    for ws in rooms[room_id]:
                        if ws != websocket:
                            await ws.send(json.dumps({'type': 'game_message', 'data': data.get('data')}))

            elif action == 'get_rooms':
                rooms_info = []
                for room_id, members in rooms.items():
                    rooms_info.append({
                        'room_id': room_id,
                        'players': len(members)
                    })
                await websocket.send(json.dumps({'type': 'send_rooms', 'rooms': rooms_info}))

            elif action == 'leave_room':
                room_id = socket_to_room.pop(websocket, None)
                if room_id and room_id in rooms:
                    rooms[room_id].discard(websocket)
                    for ws in rooms[room_id]:
                        await ws.send(json.dumps({'type': 'player_left'}))
                    if not rooms[room_id]:
                        del rooms[room_id]
                        for client in all_clients:
                            await client.send(json.dumps({'type': 'room_removed', 'room_id': room_id}))
    finally:
        all_clients.discard(websocket)
        room_id = socket_to_room.pop(websocket, None)
        if room_id and room_id in rooms:
            rooms[room_id].discard(websocket)
            for ws in rooms[room_id]:
                await ws.send(json.dumps({'type': 'player_left'}))
            if not rooms[room_id]:
                del rooms[room_id]
                for client in all_clients:
                    await client.send(json.dumps({'type': 'room_removed', 'room_id': room_id}))

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())