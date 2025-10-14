from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

class Affirmation(models.Model):
    CATEGORY_CHOICES = [
        ('self-love', 'Self Love'),
        ('motivation', 'Motivation'),
        ('calm', 'Calm'),
        ('gratitude', 'Gratitude'),
        ('healing', 'Healing'),
    ]

    text = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='self-love')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.category.title()}: {self.text[:50]}"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class DeathNoteEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DeathNote - {self.user.username}"



class DailyAffirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_affirmations')
    affirmations = models.ManyToManyField('Affirmation', related_name='daily_users')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date.isoformat()}"

class LuckCard(models.Model):
    message = models.CharField(max_length=200)
    image = models.ImageField(upload_to='luck_cards/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message