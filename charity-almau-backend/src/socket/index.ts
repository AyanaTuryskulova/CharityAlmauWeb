import { Server as HttpServer } from 'http';
import { Server } from 'socket.io';
import { env } from '../config/env';
import { verifyToken } from '../utils/jwt';
import { JwtPayload } from '../types';
import { registerChatHandlers } from './chatHandler';

let io: Server;

export function initSocket(httpServer: HttpServer) {
  io = new Server(httpServer, {
    cors: {
      origin: env.CORS_ORIGIN,
      credentials: true,
    },
  });

  // Auth middleware — verify JWT on connection
  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    if (!token) {
      return next(new Error('AUTH_REQUIRED'));
    }

    try {
      const raw = token.startsWith('Bearer ') ? token.slice(7) : token;
      const payload = verifyToken(raw);
      (socket.data as any).user = payload;
      next();
    } catch {
      next(new Error('AUTH_INVALID_TOKEN'));
    }
  });

  io.on('connection', (socket) => {
    const user: JwtPayload = socket.data.user;

    // Auto-join personal room for notifications
    socket.join(`user:${user.userId}`);

    registerChatHandlers(io, socket, user);

    socket.on('disconnect', () => {
      // cleanup if needed
    });
  });

  return io;
}

export function getIO(): Server {
  if (!io) throw new Error('Socket.IO not initialized');
  return io;
}
