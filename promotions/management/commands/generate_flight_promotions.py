from django.core.management.base import BaseCommand
from promotions.services.generation_pipeline import GenerationPipeline

class Command(BaseCommand):
    help = 'Generate flight promotions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scheduled',
            action='store_true',
            help='Run the task as a scheduled job',
        )

    def handle(self, *args, **options):
        if options['scheduled']:
            self.stdout.write("Starting scheduled generation pipeline...")
            pipeline = GenerationPipeline()
            pipeline.run_scheduled()
            self.stdout.write(self.style.SUCCESS('Successfully finished scheduled generation.'))
        else:
            self.stdout.write("Please run with --scheduled flag for now.")
