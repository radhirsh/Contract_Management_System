from rest_framework import viewsets, permissions, generics
from .models import User
from .serializers import UserSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegistrationForm, UserEditForm
from audit.models import AuditLog


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


def _has_user_admin_access(user):
    return bool(user.is_superuser or user.role == 'Admin')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        next_url = request.POST.get('next', '')
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url or 'dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form, 'next': next_url})


@login_required
def user_list(request):
    if not _has_user_admin_access(request.user):
        return HttpResponseForbidden('Only Admin users can manage users.')

    users = User.objects.all().order_by('name')
    return render(request, 'users/user_list.html', {'users': users, 'active_nav': 'users'})


@login_required
def user_edit(request, pk):
    if not _has_user_admin_access(request.user):
        return HttpResponseForbidden('Only Admin users can manage users.')

    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action='User Updated',
                target=user_obj.email,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'User "{user_obj.name}" updated.')
            return redirect('user_list_web')
    else:
        form = UserEditForm(instance=user_obj)
    return render(request, 'users/user_edit.html', {
        'form': form,
        'user_obj': user_obj,
        'active_nav': 'users',
    })


@login_required
def user_toggle_status(request, pk):
    """Enable or disable a user account."""
    if not _has_user_admin_access(request.user):
        return HttpResponseForbidden('Only Admin users can manage users.')

    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user_obj == request.user:
            messages.error(request, 'You cannot disable your own account.')
            return redirect('user_list_web')
        new_status = 'Inactive' if user_obj.status == 'Active' else 'Active'
        user_obj.status = new_status
        user_obj.is_active = (new_status == 'Active')
        user_obj.save(update_fields=['status', 'is_active'])
        AuditLog.objects.create(
            user=request.user,
            action=f'User {new_status}',
            target=user_obj.email,
            ip=request.META.get('REMOTE_ADDR', ''),
        )
        messages.success(request, f'User "{user_obj.name}" is now {new_status}.')
    return redirect('user_list_web')

