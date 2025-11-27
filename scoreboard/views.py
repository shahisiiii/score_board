# ============================================
# FILE: scoreboard/views.py
# ============================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from PIL import Image, ImageDraw, ImageFont
import io
from .models import Member, ScoreEntry, Score
from .forms import UserRegistrationForm, MemberForm, ScoreEntryForm
import datetime

def is_admin(user):
    return user.is_staff

# ============================================
# Authentication Views
# ============================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'scoreboard/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('login')

@login_required
@user_passes_test(is_admin)
def register_admin_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True
            user.save()
            messages.success(request, f'Admin {user.username} registered successfully!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'scoreboard/register_admin.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def register_user_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = False
            user.save()
            messages.success(request, f'User {user.username} registered successfully!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'scoreboard/register_user.html', {'form': form})

# ============================================
# Dashboard
# ============================================
from django.db.models import Sum

@login_required
def dashboard_view(request):
    score_entries = ScoreEntry.objects.all()[:10]
    members = Member.objects.all()
    members_score = Member.objects.annotate(
        total_score=Sum('scores__score')
    ).order_by('-total_score')
    
    context = {
        'score_entries': score_entries,
        'members': members,
        'is_admin': request.user.is_staff,
        'members_score':members_score
    }
    return render(request, 'scoreboard/dashboard.html', context)

# ============================================
# Member Management (Admin Only)
# ============================================

@login_required
@user_passes_test(is_admin)
def member_list_view(request):
    members = Member.objects.all()
    return render(request, 'scoreboard/member_list.html', {'members': members})

@login_required
@user_passes_test(is_admin)
def member_create_view(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member added successfully!')
            return redirect('member_list')
    else:
        form = MemberForm()
    
    return render(request, 'scoreboard/member_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def member_edit_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('member_list')
    else:
        form = MemberForm(instance=member)
    
    return render(request, 'scoreboard/member_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def member_delete_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Member deleted successfully!')
        return redirect('member_list')
    
    return render(request, 'scoreboard/member_confirm_delete.html', {'member': member})

# ============================================
# Score Entry Management
# ============================================

@login_required
def score_entry_list_view(request):
    entries = ScoreEntry.objects.all()
    return render(request, 'scoreboard/score_entry_list.html', {'entries': entries})

@login_required
def score_entry_detail_view(request, pk):
    entry = get_object_or_404(ScoreEntry, pk=pk)
    scores = entry.scores.all().order_by('-score')
    return render(request, 'scoreboard/score_entry_detail.html', {'entry': entry, 'scores': scores})

@login_required
@user_passes_test(is_admin)
def score_entry_create_view(request):
    members = Member.objects.all()
    
    if request.method == 'POST':
        form = ScoreEntryForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Validate 4-6 members have scores
            scored_members = []
            for member in members:
                score_value = request.POST.get(f'score_{member.id}')
                if score_value and score_value.strip():
                    scored_members.append((member, int(score_value)))
            
            if len(scored_members) < 4 or len(scored_members) > 6:
                messages.error(request, 'You must provide scores for 4-6 members only!')
                return render(request, 'scoreboard/score_entry_create.html', {
                    'form': form,
                    'members': members
                })
            
            # Create entry
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            
            # Add scores for selected members
            scored_member_ids = []
            for member, score_value in scored_members:
                Score.objects.create(entry=entry, member=member, score=score_value)
                scored_member_ids.append(member.id)
            
            # Add 0 score for remaining members
            remaining_members = Member.objects.exclude(id__in=scored_member_ids)
            for member in remaining_members:
                Score.objects.create(entry=entry, member=member, score=0)
            
            messages.success(request, 'Scores added successfully!')
            return redirect('score_entry_detail', pk=entry.id)
    else:
        form = ScoreEntryForm()
    
    return render(request, 'scoreboard/score_entry_create.html', {
        'form': form,
        'members': members
    })

# ============================================
# Scoreboard Image Generation
# ============================================

@login_required
def generate_scoreboard_image(request, pk):
    entry = get_object_or_404(ScoreEntry, pk=pk)
    scores = entry.scores.all().order_by('-score')[:8]
    
    # Image dimensions
    width, height = 1000, 1400
    bg_color = (26, 32, 44)  # Dark blue-gray
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        score_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    except:
        title_font = date_font = name_font = score_font = ImageFont.load_default()
    
    y_pos = 40
    
    # Title
    title = "🏆 SCOREBOARD 🏆"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) / 2, y_pos), title, fill=(255, 215, 0), font=title_font)
    y_pos += 90
    
    # Date
    date_text = entry.date.strftime("%B %d, %Y")
    date_bbox = draw.textbbox((0, 0), date_text, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]
    draw.text(((width - date_width) / 2, y_pos), date_text, fill=(203, 213, 225), font=date_font)
    y_pos += 60
    
    # Uploaded image
    if entry.image:
        try:
            uploaded_img = Image.open(entry.image.path)
            # Resize to fit
            max_img_width, max_img_height = 900, 350
            uploaded_img.thumbnail((max_img_width, max_img_height), Image.Resampling.LANCZOS)
            
            # Center and paste
            img_x = (width - uploaded_img.width) // 2
            img.paste(uploaded_img, (img_x, y_pos))
            y_pos += uploaded_img.height + 40
        except Exception as e:
            print(f"Error loading image: {e}")
            y_pos += 20
    
    # Draw separator
    draw.rectangle([(100, y_pos), (900, y_pos + 3)], fill=(100, 116, 139))
    y_pos += 30
    
    # Rank colors
    rank_colors = [
        (255, 215, 0),   # 1st - Gold
        (192, 192, 192), # 2nd - Silver
        (205, 127, 50),  # 3rd - Bronze
    ]
    
    # Draw scores
    for i, score in enumerate(scores):
        # Determine color
        if i < 3:
            color = rank_colors[i]
        else:
            color = (148, 163, 184)  # Gray for others
        
        # Background box
        box_height = 85
        box_y = y_pos + (i * (box_height + 10))
        
        # Draw rounded rectangle effect
        draw.rectangle([(80, box_y), (920, box_y + box_height)], 
                      fill=(45, 55, 72), outline=color, width=3)
        
        # Rank badge
        rank_text = f"#{i + 1}"
        draw.ellipse([(100, box_y + 15), (160, box_y + 70)], fill=color)
        rank_bbox = draw.textbbox((0, 0), rank_text, font=name_font)
        rank_w = rank_bbox[2] - rank_bbox[0]
        rank_h = rank_bbox[3] - rank_bbox[1]
        draw.text((130 - rank_w/2, box_y + 42 - rank_h/2), rank_text, fill=(26, 32, 44), font=name_font)
        
        # Member name
        draw.text((190, box_y + 22), score.member.name, fill=(255, 255, 255), font=name_font)
        
        # Score
        score_text = str(score.score)
        score_bbox = draw.textbbox((0, 0), score_text, font=score_font)
        score_width = score_bbox[2] - score_bbox[0]
        draw.text((880 - score_width, box_y + 20), score_text, fill=color, font=score_font)
    
    # Footer
    footer_y = height - 50
    footer_text = f"Generated by {entry.created_by.username}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=date_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(((width - footer_width) / 2, footer_y), footer_text, fill=(100, 116, 139), font=date_font)
    
    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    # Return as downloadable file
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="scoreboard_{entry.date}.png"'
    return response


@login_required
def generate_overall_scoreboard_image(request):
    # Get members with total score (change 'score_set' if you have related_name="scores")
    members = (
        Member.objects.annotate(
            total_score=Sum('scores__score')  # or 'scores__score' if you set related_name="scores"
        )
        .order_by('-total_score')[:8]
    )

    # Image setup
    width, height = 1000, 1400
    bg_color = (26, 32, 44)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts (bigger sizes)
    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90
        )
        name_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
        )
        score_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70
        )
        date_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45
        )
    except Exception:
        title_font = name_font = score_font = date_font = ImageFont.load_default()

    y_pos = 40

    # Rank colors defined HERE (important)
    rank_colors = [
        (255, 215, 0),    # 1st - Gold
        (192, 192, 192),  # 2nd - Silver
        (205, 127, 50),   # 3rd - Bronze
    ]

    # Title
    title = "🏆 OVERALL SCOREBOARD 🏆"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_w) / 2, y_pos), title, fill=(255, 215, 0), font=title_font)
    y_pos += 100

    # Date
    today_str = datetime.date.today().strftime("%B %d, %Y")
    date_bbox = draw.textbbox((0, 0), today_str, font=date_font)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text(((width - date_w) / 2, y_pos), today_str, fill=(203, 213, 225), font=date_font)
    y_pos += 60

    # Separator
    draw.rectangle([(100, y_pos), (900, y_pos + 4)], fill=(100, 116, 139))
    y_pos += 40

    # Row layout
    row_height = 160

    for i, m in enumerate(members):
        total_score = m.total_score or 0

        # Negative score -> red
        score_color = (255, 60, 60) if total_score < 0 else (255, 255, 255)

        # Outline color by rank
        if i < 3:
            outline_color = rank_colors[i]
        else:
            outline_color = (148, 163, 184)

        box_y = y_pos + i * (row_height + 20)

        # Row box
        draw.rectangle(
            [(80, box_y), (920, box_y + row_height)],
            fill=(45, 55, 72),
            outline=outline_color,
            width=5,
        )

        # Rank text
        rank_text = f"#{i + 1}"
        rank_bbox = draw.textbbox((0, 0), rank_text, font=name_font)
        draw.text(
            (100, box_y + (row_height - (rank_bbox[3] - rank_bbox[1])) / 2),
            rank_text,
            fill=outline_color,
            font=name_font,
        )

        # Member name
        name_text = m.name
        draw.text((300, box_y + 40), m.name, fill=(255,255,255), font=name_font)


        # Score (right aligned)
        score_text = str(total_score)
        score_bbox = draw.textbbox((0, 0), score_text, font=score_font)
        score_w = score_bbox[2] - score_bbox[0]
        draw.text((850 - score_w, box_y + 30), score_text, fill=score_color, font=score_font)


    # Footer
    footer = "Overall Scoreboard (Auto-generated)"
    footer_bbox = draw.textbbox((0, 0), footer, font=date_font)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((width - footer_w) / 2, height - 60),
        footer,
        fill=(100, 116, 139),
        font=date_font,
    )

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", quality=95)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="image/png")
    response["Content-Disposition"] = 'attachment; filename="overall_scoreboard.png"'
    return response
