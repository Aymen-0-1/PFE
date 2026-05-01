// Toggle sidebar on mobile
document.getElementById('sidebarToggle')?.addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('sidebar-hidden');
});

// User menu toggle
const userMenuBtn = document.getElementById('userMenuBtn');
const userMenu = document.getElementById('userMenu');
if (userMenuBtn && userMenu) {
    userMenuBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        userMenu.classList.toggle('hidden');
    });
    
    document.addEventListener('click', function(event) {
        if (!userMenuBtn.contains(event.target) && !userMenu.contains(event.target)) {
            userMenu.classList.add('hidden');
        }
    });
}

// Language switcher
const langBtn = document.getElementById('langBtn');
const langMenu = document.getElementById('langMenu');
if (langBtn && langMenu) {
    langBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        langMenu.classList.toggle('hidden');
    });
    
    document.querySelectorAll('.lang-option').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.dataset.lang;
            fetch('/set-language/' + lang)
                .then(() => location.reload());
        });
    });
    
    document.addEventListener('click', function(event) {
        if (!langBtn.contains(event.target) && !langMenu.contains(event.target)) {
            langMenu.classList.add('hidden');
        }
    });
}
// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// Notifications
const notificationsBtn = document.getElementById('notificationsBtn');
const notificationsDropdown = document.getElementById('notificationsDropdown');
const notificationsList = document.getElementById('notificationsList');
const notificationsCount = document.getElementById('notificationsCount');

async function loadNotifications() {
    try {
        const response = await fetch('/doctor/api/notifications');
        const data = await response.json();
        
        if (data.unread_count > 0) {
            notificationsCount.textContent = data.unread_count;
            notificationsCount.classList.remove('hidden');
        } else {
            notificationsCount.classList.add('hidden');
        }
        
        if (notificationsList) {
            if (data.notifications.length === 0) {
notificationsList.innerHTML = '<div class="p-4 text-center" style="color: #374151;">No new notifications</div>';
} else {
notificationsList.innerHTML = data.notifications.map(n => `
<div class="p-3 hover:bg-gray-50 transition border-b border-gray-100" data-id="${n.id}" style="color: #1f2937;">
    <div class="flex justify-between items-start">
        <div class="flex-1 pr-2">
            <p class="text-sm font-semibold" style="color: #1f2937;">📋 ${escapeHtml(n.message)}</p>
            <p class="text-xs mt-1" style="color: #6b7280;">🕐 ${n.created_at}</p>
        </div>
        <div class="flex gap-1">
            <button onclick="respondToNotification(${n.id}, 'accept')" 
                    class="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition">
                ✓
            </button>
            <button onclick="respondToNotification(${n.id}, 'reject')" 
                    class="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition">
                ✗
            </button>
        </div>
    </div>
</div>
`).join('');
}
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function respondToNotification(notificationId, action) {
    try {
        const response = await fetch(`/doctor/api/notifications/${notificationId}/respond`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadNotifications(); // تحديث القائمة
            location.reload(); // تحديث الصفحة لتحديث قائمة المرضى
        }
    } catch (error) {
        console.error('Error responding to notification:', error);
    }
}

if (notificationsBtn) {
    notificationsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notificationsDropdown.classList.toggle('hidden');
        loadNotifications();
    });
    
    document.addEventListener('click', () => {
        notificationsDropdown.classList.add('hidden');
    });
}
// Auto-dismiss flash messages
document.querySelectorAll('.flash-message').forEach(msg => {
    const duration = parseInt(msg.getAttribute('data-auto-dismiss')) || 5000;
    setTimeout(() => {
        if (msg && msg.remove) msg.remove();
    }, duration);
});
