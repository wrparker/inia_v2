from django import forms
from captcha.fields import ReCaptchaField
from inia.models import SpeciesType


class ContactForm(forms.Form):
    name = forms.CharField(label='Your Name', max_length=100)
    email = forms.EmailField(label='Your Email')
    comment = forms.CharField(widget=forms.Textarea(), label="Question/Comment:")
    captcha = ReCaptchaField()


class MultisearchForm(forms.Form):
    ANALYSIS_TYPE = [
        ('Multiple Gene Search', 'multiple'),
        ('Gene Network', 'gene_network'),
        ('Overrepresentation', 'overrepresentation'),
        ('Dataset Network', 'dataset_network'),
    ]
    SPECIES = [
        ('Mouse', SpeciesType.MUS_MUSCULUS),
        ('Rat', SpeciesType.RATTUS_NORVEGICUS),
        ('Human', SpeciesType.HOMO_SAPIENS)
    ]
    DATASETS = [('All datasets', 'all'), ('Select custom datasets...', 'custom')]

    type = forms.ChoiceField(choices=ANALYSIS_TYPE, label='Type of analysis:',
                             widget=forms.RadioSelect())
    title = forms.CharField(widget=forms.Textarea(),
                label='Title for this dataset (optional, can be added/edited later):')
    species = forms.ChoiceField(choices=SPECIES, label='Species:')
    genes = forms.CharField(widget=forms.Textarea(), label="Genes:")
    datasets = forms.ChoiceField(choices=DATASETS, label='Datasets:',
                                 widget=forms.RadioSelect())