from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = 'Update all "Med" difficulty values to "Medium" in the database'

    def handle(self, *args, **options):
        # Find all questions with 'Med' difficulty
        questions = Question.objects.filter(difficulty='Med')
        count = questions.count()
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING('No questions found with "Med" difficulty.')
            )
            return
        
        # Update all 'Med' to 'Medium'
        updated_count = questions.update(difficulty='Medium')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} questions from "Med" to "Medium" difficulty.'
            )
        )
        
        # Also check for other variations
        other_variations = Question.objects.filter(
            difficulty__in=['med', 'MED', 'Med']
        )
        other_count = other_variations.count()
        
        if other_count > 0:
            other_variations.update(difficulty='Medium')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Also updated {other_count} questions with other "Med" variations to "Medium".'
                )
            )
        
        # Show summary
        total_updated = updated_count + other_count
        self.stdout.write(
            self.style.SUCCESS(
                f'Total questions updated: {total_updated}'
            )
        ) 