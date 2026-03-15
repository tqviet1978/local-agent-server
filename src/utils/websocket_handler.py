"""
WebSocket Support for Local Agent Server

REQUIREMENTS:
    pip install flask-socketio python-socketio eventlet --break-system-packages

USAGE:
    1. Install dependencies above
    2. In app.py, add:
        from utils.websocket_handler import init_websocket
        socketio = init_websocket(app)
    3. Run with: socketio.run(app, host=..., port=...)
    
FEATURES:
    - Real-time file watching
    - Live command execution
    - Repository updates notifications
"""

try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    from flask import request
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("⚠️  WebSocket support disabled: flask-socketio not installed")
    print("    Install with: pip install flask-socketio python-socketio eventlet --break-system-packages")

from auth import verify_token
import os
import time
from threading import Thread
from pathlib import Path


if SOCKETIO_AVAILABLE:
    socketio = None
    
    def init_websocket(app):
        """
        Initialize WebSocket support
        
        Args:
            app: Flask application instance
        
        Returns:
            SocketIO instance
        """
        global socketio
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=False
        )
        
        @socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            # Verify auth token
            token = request.args.get('token')
            if not verify_token(token):
                return False  # Reject connection
            
            print(f"✓ WebSocket client connected: {request.sid}")
            emit('connected', {'status': 'ok', 'sid': request.sid})
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print(f"✗ WebSocket client disconnected: {request.sid}")
        
        @socketio.on('watch_repository')
        def handle_watch_repository(data):
            """
            Start watching a repository for file changes
            
            Data:
                - repository: str - Repository code
                - patterns: list[str] - File patterns to watch (e.g., ["*.py", "src/**/*"])
            """
            repository = data.get('repository')
            patterns = data.get('patterns', ['**/*'])
            
            if not repository:
                emit('error', {'message': 'Missing repository'})
                return
            
            # Join room for this repository
            room = f"repo_{repository}"
            join_room(room)
            
            emit('watching', {
                'repository': repository,
                'patterns': patterns,
                'room': room
            })
            
            # Start file watcher thread (simplified example)
            # In production, use watchdog library
            # Thread(target=watch_files, args=(repository, patterns, room)).start()
        
        @socketio.on('stop_watching')
        def handle_stop_watching(data):
            """Stop watching a repository"""
            repository = data.get('repository')
            room = f"repo_{repository}"
            leave_room(room)
            emit('stopped_watching', {'repository': repository})
        
        @socketio.on('execute_command')
        def handle_execute_command(data):
            """
            Execute command and stream output via WebSocket
            
            Data:
                - repository: str
                - command: str
            """
            repository = data.get('repository')
            command = data.get('command')
            
            if not repository or not command:
                emit('error', {'message': 'Missing repository or command'})
                return
            
            # Execute command in thread and emit output
            Thread(target=execute_command_ws, args=(repository, command, request.sid)).start()
        
        print("✓ WebSocket support initialized")
        print("  - Connect: ws://host:port/socket.io/?token=YOUR_TOKEN")
        print("  - Events: watch_repository, stop_watching, execute_command")
        
        return socketio
    
    
    def execute_command_ws(repository, command, sid):
        """Execute command and emit output via WebSocket"""
        import subprocess
        from config import get_repo_manager
        from utils.path_utils import get_safe_path
        
        try:
            repo_manager = get_repo_manager()
            repo_path = get_safe_path(repo_manager, repository, "")
            
            # Send start event
            socketio.emit('command_started', {
                'repository': repository,
                'command': command
            }, room=sid)
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(repo_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Stream stdout
            for line in process.stdout:
                socketio.emit('command_output', {
                    'type': 'stdout',
                    'content': line.rstrip()
                }, room=sid)
            
            # Stream stderr
            for line in process.stderr:
                socketio.emit('command_output', {
                    'type': 'stderr',
                    'content': line.rstrip()
                }, room=sid)
            
            # Wait for completion
            returncode = process.wait()
            
            # Send completion
            socketio.emit('command_completed', {
                'returncode': returncode,
                'success': returncode == 0
            }, room=sid)
        
        except Exception as e:
            socketio.emit('error', {'message': str(e)}, room=sid)
    
    
    def watch_files(repository, patterns, room):
        """
        Watch files for changes (simplified example)
        
        In production, use watchdog library:
            pip install watchdog --break-system-packages
        """
        # This is a placeholder
        # Real implementation would use watchdog.observers.Observer
        pass
    
    
    def broadcast_file_change(repository, file_path, event_type):
        """Broadcast file change to all watchers"""
        if socketio:
            room = f"repo_{repository}"
            socketio.emit('file_changed', {
                'repository': repository,
                'path': file_path,
                'event': event_type,
                'timestamp': time.time()
            }, room=room)

else:
    # Dummy functions when socketio not available
    def init_websocket(app):
        print("⚠️  WebSocket support not available")
        print("    Install: pip install flask-socketio python-socketio eventlet --break-system-packages")
        return None
    
    def broadcast_file_change(repository, file_path, event_type):
        pass
