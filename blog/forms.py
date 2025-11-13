from django import forms
from .models import Blog, Comment


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'description', 'video_url', 'preview_image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Description'}),
            'video_url': forms.ClearableFileInput(),
        }  

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
