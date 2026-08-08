from django.core.management.base import BaseCommand

from apps.promotions.services.generation_pipeline import GenerationPipeline


class Command(BaseCommand):
    help = "Generate flight promotions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--scheduled",
            action="store_true",
            help="Run the task as a scheduled job",
        )

    def handle(self, *args, **options):
        is_scheduled = options["scheduled"]
        mode = "SCHEDULED" if is_scheduled else "MANUAL"
        self.stdout.write(f"Starting {mode} generation pipeline...")

        pipeline = GenerationPipeline()
        pipeline.run(is_scheduled=is_scheduled)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully finished {mode} generation.")
        )
