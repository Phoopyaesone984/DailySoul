from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

class Affirmation(models.Model):
    text = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(
        upload_to='affirmations/',
        blank=True,
        null=True,
        help_text='Optional: upload a thumbnail for this affirmation'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.text[:50] + '...') if len(self.text) > 50 else self.text

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


from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class LuckCard(models.Model):
    # Simple model - just image and message
    image = models.ImageField(upload_to='luck_cards/')
    message = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Card: {self.message[:50]}"


class DailyPileDraw(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cards = models.ManyToManyField(LuckCard, through='PileCardSelection')
    date = models.DateField(default=timezone.now)
    draw_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date} - Draws: {self.draw_count}"


class PileCardSelection(models.Model):
    daily_draw = models.ForeignKey(DailyPileDraw, on_delete=models.CASCADE)
    card = models.ForeignKey(LuckCard, on_delete=models.CASCADE)
    position = models.IntegerField(choices=[(1, 'Position 1'), (2, 'Position 2'), (3, 'Position 3')])

    class Meta:
        unique_together = ['daily_draw', 'position']

    def __str__(self):
        return f"Position {self.position}"