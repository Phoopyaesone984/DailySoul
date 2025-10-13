from django.contrib import admin
from .models import JournalEntry,Affirmation,DeathNoteEntry,LuckCard

admin.site.register(Affirmation)
admin.site.register(JournalEntry)
admin.site.register(DeathNoteEntry)
admin.site.register(LuckCard)