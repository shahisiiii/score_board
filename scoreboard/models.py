# ============================================
# FILE: scoreboard/models.py
# ============================================

from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ScoreEntry(models.Model):
    date = models.DateField()
    image = models.ImageField(upload_to='score_images/')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = "Score Entries"
    
    def __str__(self):
        return f"Scores for {self.date}"

class Score(models.Model):
    entry = models.ForeignKey(ScoreEntry, on_delete=models.CASCADE, related_name='scores')
    member = models.ForeignKey(Member, on_delete=models.CASCADE,related_name="scores")
    score = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('entry', 'member')
        ordering = ['-score']
    
    def __str__(self):
        return f"{self.member.name}: {self.score}"
