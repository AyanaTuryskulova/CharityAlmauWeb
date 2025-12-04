#!/usr/bin/env python3
import re

# 1. Add CHANNEL_LAYERS to settings.py
with open('./CharityAlmaWeb/settings.py', 'r', encoding='utf8') as f:
    content = f.read()

pattern = r'(ASGI_APPLICATION = "CharityAlmaWeb\.asgi\.application")\n'
replacement = r'\1\n\n# Channels: channel layer configuration\nCHANNEL_LAYERS = {\n    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}\n}\n'
content = re.sub(pattern, replacement, content)

with open('./CharityAlmaWeb/settings.py', 'w', encoding='utf8') as f:
    f.write(content)

print('✓ CHANNEL_LAYERS added to settings.py')

# 2. Update asgi.py with ProtocolTypeRouter
asgi_content = '''"""
ASGI config for CharityAlmaWeb project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.apps.chat.routing as chat_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CharityAlmaWeb.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(chat_routing.websocket_urlpatterns)),
})
'''

with open('./CharityAlmaWeb/asgi.py', 'w', encoding='utf8') as f:
    f.write(asgi_content)

print('✓ asgi.py updated with ProtocolTypeRouter')

# 3. Add WebSocket client JS to detail.html
with open('./core/apps/chat/templates/chat/detail.html', 'r', encoding='utf8') as f:
    detail_content = f.read()

# Find the closing </style> tag and add a <script> block after it
ws_script = '''

<script>
    (function(){
        const chatId = '{{ chat.id }}';
        const messagesContainer = document.getElementById('messagesContainer');
        const form = document.querySelector('.detail-form');
        const textarea = form ? form.querySelector('textarea[name="text"]') : null;

        function scrollToBottom(){
            if (messagesContainer) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }

        setTimeout(scrollToBottom, 50);

        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${wsScheme}://${window.location.host}/ws/chat/${chatId}/`;
        let socket;

        try {
            socket = new WebSocket(wsUrl);
        } catch (e) {
            console.warn('WebSocket init failed', e);
        }

        if (socket) {
            socket.onopen = () => console.log('WebSocket connected to', wsUrl);

            socket.onmessage = function(e){
                try {
                    const data = JSON.parse(e.data);
                    if (data.text || data.image_url) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'message other';

                        const bubble = document.createElement('div');
                        bubble.className = 'message-bubble';

                        if (data.image_url) {
                            const img = document.createElement('img');
                            img.src = data.image_url;
                            img.className = 'msg-image';
                            bubble.appendChild(img);
                        }
                        if (data.text) {
                            const p = document.createElement('p');
                            p.textContent = data.text;
                            bubble.appendChild(p);
                        }

                        wrapper.appendChild(bubble);
                        if (messagesContainer) {
                            messagesContainer.appendChild(wrapper);
                            scrollToBottom();
                        }
                    }
                } catch(err){ console.error('WS message parse error', err); }
            };

            socket.onclose = function(){ console.log('WebSocket closed'); };
            socket.onerror = function(e){ console.error('WebSocket error', e); };
        }

        // Intercept form submit: prefer WebSocket for text-only messages
        if (form) {
            form.addEventListener('submit', function(ev){
                const fileInput = form.querySelector('input[type="file"]');
                if (fileInput && fileInput.files && fileInput.files.length > 0) {
                    return;
                }

                ev.preventDefault();
                const text = textarea ? textarea.value.trim() : '';
                if (!text) return;

                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ text: text }));
                    
                    const own = document.createElement('div');
                    own.className = 'message own';
                    const b = document.createElement('div'); 
                    b.className = 'message-bubble';
                    const p = document.createElement('p'); 
                    p.textContent = text;
                    b.appendChild(p); 
                    own.appendChild(b);
                    if (messagesContainer) {
                        messagesContainer.appendChild(own);
                        scrollToBottom();
                    }
                    
                    if (textarea) textarea.value = '';
                } else {
                    form.submit();
                }
            });
        }
    })();
</script>
'''

# Check if script tag already exists; if not, add it before the closing </html>
if '<script>' not in detail_content or '/ws/chat' not in detail_content:
    if detail_content.endswith('</html>\n'):
        detail_content = detail_content[:-9] + ws_script + '\n</html>\n'
    elif detail_content.endswith('</html>'):
        detail_content = detail_content[:-7] + ws_script + '\n</html>'
    else:
        detail_content += ws_script

    with open('./core/apps/chat/templates/chat/detail.html', 'w', encoding='utf8') as f:
        f.write(detail_content)

    print('✓ WebSocket client added to detail.html')
else:
    print('⚠ WebSocket client already present in detail.html, skipping')

print('\n✓ All patches applied successfully!')
