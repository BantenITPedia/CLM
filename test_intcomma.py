from django.contrib.humanize.templatetags.humanize import intcomma

# Test intcomma function
test_values = [22500000000, "22500000000", 12345, "1234567.89"]

for val in test_values:
    result = intcomma(val)
    print(f"intcomma({val!r}) = {result!r}")
