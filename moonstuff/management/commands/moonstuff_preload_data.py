from django.core.management.base import BaseCommand

from ...tasks import load_types_and_mats


class Command(BaseCommand):
    help = 'Preloads type and material data required for moonstuff.'

    def handle(self, *args, **options):
        categories = [25]
        groups = [18, 423, 427, 1406]

        self.stdout.write("Moonstuff Data Loader")
        self.stdout.write("=====================")

        self.stdout.write("This command will start loading type and material data required by the "
                          "moonstuff app.")

        self.stdout.write("This process can take a while to complete "
                          "and can create significant load on your system.")

        answer = input("Are you sure you would like to proceed? [y/N]: ")
        if answer.lower() == 'y':
            load_types_and_mats.delay(
                category_ids=categories, group_ids=groups, type_ids=None, force_loading_dogma=True
            )
            self.stdout.write(self.style.SUCCESS("Data loading has been started."))
        else:
            self.stdout.write(self.style.WARNING("Aborted."))
