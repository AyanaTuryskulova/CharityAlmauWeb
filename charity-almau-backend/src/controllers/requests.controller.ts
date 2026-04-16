import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as requestsService from '../services/requests.service';

export async function createRequest(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const request = await requestsService.createRequest(req.body, req.user!.userId);
    res.status(201).json({ success: true, data: request });
  } catch (err) {
    next(err);
  }
}

export async function getIncomingRequests(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await requestsService.getIncomingRequests(req.query as any, req.user!.userId);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function getOutgoingRequests(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await requestsService.getOutgoingRequests(req.query as any, req.user!.userId);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function acceptRequest(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const request = await requestsService.acceptRequest(req.params.id as string, req.user!.userId);
    res.json({ success: true, data: request });
  } catch (err) {
    next(err);
  }
}

export async function rejectRequest(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const request = await requestsService.rejectRequest(req.params.id as string, req.user!.userId);
    res.json({ success: true, data: request });
  } catch (err) {
    next(err);
  }
}

export async function cancelRequest(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const request = await requestsService.cancelRequest(req.params.id as string, req.user!.userId);
    res.json({ success: true, data: request });
  } catch (err) {
    next(err);
  }
}
