from django.shortcuts import render

def notifications_list(request):
    return render(request, 'notifications/notifications_list.html', {'active_nav': 'notifications'})