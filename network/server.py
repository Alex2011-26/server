import asyncio
import json
import random
import string
import websockets
import os

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
                player_name = data.get('player_name', 'Unknown')
                room_id = generate_room_id()
                rooms[room_id] = {websocket}
                socket_to_room[websocket] = {
                    "room_id": room_id,
                    "name": player_name,
                    "leader": True
                }
                await websocket.send(json.dumps({
                    'type': 'room_created',
                    'room_id': room_id,
                    'players': [{"name": player_name, "leader": True}]
                }))
                for client in all_clients:
                    await client.send(json.dumps({
                        'type': 'room_added',
                        'room_id': room_id,
                        'players': 1
                    }))

            elif action == 'join_room':
                room_id = data['room_id']
                player_name = data.get('player_name', 'Unknown')
                if room_id in rooms and len(rooms[room_id]) < 2:
                    rooms[room_id].add(websocket)
                    socket_to_room[websocket] = {
                        "room_id": room_id,
                        "name": player_name,
                        "leader": False
                    }
                    players_info = []
                    for ws in rooms[room_id]:
                        info = socket_to_room.get(ws, {})
                        players_info.append({
                            "name": info.get("name", "Unknown"),
                            "leader": info.get("leader", False)
                        })
                    for ws in rooms[room_id]:
                        await ws.send(json.dumps({
                            'type': 'player_joined',
                            'count': len(rooms[room_id]),
                            'room_id': room_id,
                            'players': players_info
                        }))
                    for client in all_clients:
                        if client not in rooms[room_id]:
                            await client.send(json.dumps({
                                'type': 'room_updated',
                                'room_id': room_id,
                                'players': len(rooms[room_id])
                            }))
                else:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Room not found or full'}))

            elif action == 'start_game':
                room_data = socket_to_room.get(websocket)
                if room_data and room_data.get("leader") and room_data["room_id"] in rooms:
                    room_id = room_data["room_id"]
                    if len(rooms[room_id]) == 2:
                        for ws in rooms[room_id]:
                            is_leader = socket_to_room[ws].get("leader", False)
                            await ws.send(json.dumps({
                                'type': 'game_started',
                                'leader': is_leader
                            }))
                    else:
                        await websocket.send(json.dumps({'type': 'error', 'message': 'Need 2 players to start'}))
                else:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Only leader can start the game'}))

            elif action == 'sync_field':
                room_data = socket_to_room.get(websocket)
                if room_data and room_data["room_id"] in rooms:
                    room_id = room_data["room_id"]
                    for ws in rooms[room_id]:
                        if ws != websocket:
                            await ws.send(json.dumps({
                                'type': 'field_update',
                                'back_pattern': data['back_pattern'],
                                'color_to_stay': data['color_to_stay']
                            }))

            elif action == 'send_position':
                room_data = socket_to_room.get(websocket)
                if room_data:
                    room_id = room_data['room_id']
                    if room_id in rooms:
                        for ws in rooms[room_id]:
                            if ws != websocket:
                                await ws.send(json.dumps({'type': 'opponent_position', 'position': data.get('position')}))

            elif action == 'game_over':
                room_data = socket_to_room.get(websocket)
                leader_state = data.get('leader_state', None)
                player_state = data.get('player_state', None)
                if room_data and room_data["room_id"] in rooms:
                    room_id = room_data["room_id"]
                    for ws in rooms[room_id]:
                        await ws.send(json.dumps({'type': 'return_to_lobby',
                                                  'leader_state': leader_state,
                                                  'player_state': player_state}))

            elif action == 'message':
                room_data = socket_to_room.get(websocket)
                if room_data:
                    room_id = room_data["room_id"]
                    if room_id in rooms:
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
                room_data = socket_to_room.pop(websocket, None)
                if room_data:
                    room_id = room_data["room_id"]
                    if room_id in rooms:
                        rooms[room_id].discard(websocket)
                        if rooms[room_id]:
                            players_left = []
                            for ws in rooms[room_id]:
                                info = socket_to_room.get(ws, {})
                                players_left.append({
                                    "name": info.get("name", "Unknown"),
                                    "leader": info.get("leader", False)
                                })
                            for ws in rooms[room_id]:
                                await ws.send(json.dumps({
                                    'type': 'player_left',
                                    'players': players_left
                                }))
                            for client in all_clients:
                                await client.send(json.dumps({
                                    'type': 'room_updated',
                                    'room_id': room_id,
                                    'players': len(rooms[room_id])
                                }))
                        else:
                            del rooms[room_id]
                            for client in all_clients:
                                await client.send(json.dumps({'type': 'room_removed', 'room_id': room_id}))

            elif action == 'leave_game':
                room_data = socket_to_room.get(websocket)
                if room_data:
                    room_id = room_data["room_id"]
                    if room_id in rooms:
                        if room_data.get("leader"):
                            for ws in rooms[room_id]:
                                await ws.send(json.dumps({'type': 'return_to_menu'}))
                            for ws in rooms[room_id]:
                                socket_to_room.pop(ws, None)
                            del rooms[room_id]
                            for client in all_clients:
                                await client.send(json.dumps({'type': 'room_removed', 'room_id': room_id}))
                        else:
                            rooms[room_id].discard(websocket)
                            socket_to_room.pop(websocket, None)
                            await websocket.send(json.dumps({'type': 'return_to_menu'}))
                            players_left = []
                            for ws in rooms[room_id]:
                                info = socket_to_room.get(ws, {})
                                players_left.append({
                                    "name": info.get("name", "Unknown"),
                                    "leader": info.get("leader", False)
                                })
                            for ws in rooms[room_id]:
                                await ws.send(json.dumps({
                                    'type': 'player_left',
                                    'players': players_left
                                }))
                            for client in all_clients:
                                await client.send(json.dumps({
                                    'type': 'room_updated',
                                    'room_id': room_id,
                                    'players': len(rooms[room_id])
                                }))

            elif action == 'check_colors':
                room_data = socket_to_room.get(websocket)
                if room_data:
                    room_id = room_data["room_id"]
                    if room_id in rooms:
                        for ws in rooms[room_id]:
                            await ws.send(json.dumps({'type': 'checking_colors'}))

            elif action == 'send_colors':
                room_data = socket_to_room.get(websocket)
                if room_data:
                    room_id = room_data["room_id"]
                    if room_id in rooms:
                        for ws in rooms[room_id]:
                            if ws != websocket:
                                await ws.send(json.dumps({'type': 'sent_color', 'color': data['color']}))

    finally:
        all_clients.discard(websocket)
        room_data = socket_to_room.pop(websocket, None)
        if room_data:
            room_id = room_data["room_id"]
            if room_id in rooms:
                rooms[room_id].discard(websocket)
                if rooms[room_id]:
                    players_left = []
                    for ws in rooms[room_id]:
                        info = socket_to_room.get(ws, {})
                        players_left.append({
                            "name": info.get("name", "Unknown"),
                            "leader": info.get("leader", False)
                        })
                    for ws in rooms[room_id]:
                        await ws.send(json.dumps({'type': 'player_left', 'players': players_left}))
                    for client in all_clients:
                        await client.send(json.dumps({
                            'type': 'room_updated',
                            'room_id': room_id,
                            'players': len(rooms[room_id])
                        }))
                else:
                    del rooms[room_id]
                    for client in all_clients:
                        await client.send(json.dumps({'type': 'room_removed', 'room_id': room_id}))

async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())