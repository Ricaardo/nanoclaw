import { describe, it, expect, beforeEach } from 'vitest';

import { _initTestDatabase, getAllChats, storeChatMetadata } from './db.js';
import { getAvailableGroups, _setRegisteredGroups } from './index.js';

beforeEach(() => {
  _initTestDatabase();
  _setRegisteredGroups({});
});

// --- JID ownership patterns ---

describe('JID ownership patterns', () => {
  // These test the patterns that will become ownsJid() on the Channel interface

  it('WhatsApp group JID: ends with @g.us', () => {
    const jid = '12345678@g.us';
    expect(jid.endsWith('@g.us')).toBe(true);
  });

  it('WhatsApp DM JID: ends with @s.whatsapp.net', () => {
    const jid = '12345678@s.whatsapp.net';
    expect(jid.endsWith('@s.whatsapp.net')).toBe(true);
  });

  it('unknown JID format: does not match WhatsApp patterns', () => {
    const jid = 'unknown:12345';
    expect(jid.endsWith('@g.us')).toBe(false);
    expect(jid.endsWith('@s.whatsapp.net')).toBe(false);
  });
});

// --- getAvailableGroups ---

describe('getAvailableGroups', () => {
  it('returns only imessage: JIDs', () => {
    storeChatMetadata('imessage:+1234567890', '2024-01-01T00:00:01.000Z', 'Chat 1');
    storeChatMetadata('imessage:+0987654321', '2024-01-01T00:00:02.000Z', 'Chat 2');

    const groups = getAvailableGroups();
    expect(groups).toHaveLength(2);
    expect(groups.every((g) => g.jid.startsWith('imessage:'))).toBe(true);
  });

  it('excludes __group_sync__ sentinel', () => {
    storeChatMetadata('__group_sync__', '2024-01-01T00:00:00.000Z');
    storeChatMetadata('imessage:+1234567890', '2024-01-01T00:00:01.000Z', 'Chat');

    const groups = getAvailableGroups();
    expect(groups).toHaveLength(1);
    expect(groups[0].jid).toBe('imessage:+1234567890');
  });

  it('marks registered groups correctly', () => {
    storeChatMetadata('imessage:+1111111111', '2024-01-01T00:00:01.000Z', 'Registered');
    storeChatMetadata('imessage:+2222222222', '2024-01-01T00:00:02.000Z', 'Unregistered');

    _setRegisteredGroups({
      'imessage:+1111111111': {
        name: 'Registered',
        folder: 'registered',
        trigger: '@Andy',
        added_at: '2024-01-01T00:00:00.000Z',
      },
    });

    const groups = getAvailableGroups();
    const reg = groups.find((g) => g.jid === 'imessage:+1111111111');
    const unreg = groups.find((g) => g.jid === 'imessage:+2222222222');

    expect(reg?.isRegistered).toBe(true);
    expect(unreg?.isRegistered).toBe(false);
  });

  it('returns groups ordered by most recent activity', () => {
    storeChatMetadata('imessage:+1111111111', '2024-01-01T00:00:01.000Z', 'Old');
    storeChatMetadata('imessage:+2222222222', '2024-01-01T00:00:05.000Z', 'New');
    storeChatMetadata('imessage:+3333333333', '2024-01-01T00:00:03.000Z', 'Mid');

    const groups = getAvailableGroups();
    expect(groups[0].jid).toBe('imessage:+2222222222');
    expect(groups[1].jid).toBe('imessage:+3333333333');
    expect(groups[2].jid).toBe('imessage:+1111111111');
  });

  it('returns empty array when no chats exist', () => {
    const groups = getAvailableGroups();
    expect(groups).toHaveLength(0);
  });
});
