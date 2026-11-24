from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matchMaker", "0021_gameaccount_rank_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="gameaccount",
            name="game_tag",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
