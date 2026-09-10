from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("predictions", "0001_initial")]

    operations = [migrations.AddField(model_name="predictionrun", name="baseline_probability", field=models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True))]
