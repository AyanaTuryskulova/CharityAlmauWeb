import { ConfidentialClientApplication } from '@azure/msal-node';
import prisma from '../config/prisma';
import { env } from '../config/env';
import { signToken } from '../utils/jwt';
import { AUTH_NOT_ALMAU_EMAIL, AUTH_MSAL_FAILED } from '../utils/errors';

const msalConfig = {
  auth: {
    clientId: env.MSAL_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${env.MSAL_TENANT_ID}`,
    clientSecret: env.MSAL_CLIENT_SECRET,
  },
};

const msalClient = new ConfidentialClientApplication(msalConfig);

const scopes = ['user.read', 'openid', 'profile', 'email'];

export function getLoginUrl(): string {
  const params = new URLSearchParams({
    client_id: env.MSAL_CLIENT_ID,
    response_type: 'code',
    redirect_uri: env.MSAL_REDIRECT_URI,
    scope: scopes.join(' '),
    response_mode: 'query',
  });
  return `https://login.microsoftonline.com/${env.MSAL_TENANT_ID}/oauth2/v2.0/authorize?${params}`;
}

export async function handleCallback(code: string) {
  let tokenResponse;
  try {
    tokenResponse = await msalClient.acquireTokenByCode({
      code,
      scopes,
      redirectUri: env.MSAL_REDIRECT_URI,
    });
  } catch {
    throw AUTH_MSAL_FAILED();
  }

  const email = (tokenResponse.account?.username || '').toLowerCase();
  const name = tokenResponse.account?.name || email.split('@')[0];

  if (!email.endsWith('@almau.edu.kz')) {
    throw AUTH_NOT_ALMAU_EMAIL();
  }

  const user = await prisma.user.upsert({
    where: { email },
    update: { name },
    create: { email, name },
  });

  const token = signToken({ userId: user.id, email: user.email, role: user.role });

  return { token, user };
}

export async function devLogin(email: string, name: string) {
  if (!email.endsWith('@almau.edu.kz')) {
    throw AUTH_NOT_ALMAU_EMAIL();
  }

  const user = await prisma.user.upsert({
    where: { email },
    update: { name },
    create: { email, name },
  });

  const token = signToken({ userId: user.id, email: user.email, role: user.role });

  return { token, user };
}

export async function getMe(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { _count: { select: { listings: true } } },
  });
  return user;
}
