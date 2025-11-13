from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Blog, Comment
from .forms import BlogForm, CommentForm
from travelbook.utils.telegram_notify import send_telegram_message
from django.utils import timezone







def blog_list(request):
    posts = Blog.objects.all().filter(published=True)
    return render(request, 'blog/blog_list.html', {'posts': posts})

def blog_detail(request, pk):
    post = get_object_or_404(Blog, pk=pk, published=True)
    comments = post.comments.all().order_by('created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You need to log in to comment.")
            return redirect('users:login')

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.success(request, "Comment added!")
            return redirect('blog:detail', pk=post.pk)
    else:
        form = CommentForm()

    return render(request, 'blog/blog_detail.html', {'post': post, 'comments': comments, 'form': form})

@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)  
            blog.owner = request.user       
            blog.save()                     
            return redirect('blog:list')
    else:
        form = BlogForm()
    return render(request, 'blog/blog_detail.html', {'form': form, 'action': 'create'})

@login_required
def blog_edit(request, pk):
    post = get_object_or_404(Blog, pk=pk, author=request.user)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog post updated!")
            return redirect('blog:detail', pk=post.pk)
    else:
        form = BlogForm(instance=post)
    return render(request, 'blog/blog_form.html', {'form': form, 'action': 'edit'})







def blog_form(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            blog.owner = request.user
            blog.created_at = timezone.now()
            blog.save()
            messages.success(request, "New blog post published successfully!")

           
            try:
                msg = (
                    f"📰 <b>New Blog Post Published!</b>\n"
                    f"✍️ Author: <b>{blog.author.username}</b>\n"
                    f"📖 Title: <b>{blog.title}</b>\n"
                    f"🕒 Time: {blog.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🔗 Link: /blog/{blog.id}/"
                )
                send_telegram_message(msg)
            except Exception as e:
                print(f"Telegram send failed: {e}")

            return redirect('blog:list')
    else:
        form = BlogForm()

    return render(request, 'blog/blog_form.html', {'form': form})