'''
models.py contains the ORM structure and programmable database structure.
'''
from django.db import models
from django.contrib.postgres.fields import JSONField  # We're stuck to postgres now.


class SpeciesType(object):
    ''' The values of these enums are based on the NCBI taxonomy ID:
    https://www.ncbi.nlm.nih.gov/Taxonomy
    '''
    UNKNOWN = 'UNKNOWN'
    HOMO_SAPIENS = 'HOMO_SAPIENS'  # Human tax id: 9606
    MUS_MUSCULUS = 'MUS_MUSCULUS'    # Mouse tax id: 10090
    RATTUS_NORVEGICUS = 'RATTUS_NORVEGICUS'  # Rat 10116

    SPECIES_CHOICES = (
        (HOMO_SAPIENS, 'HOMO_SAPIENS'),
        (MUS_MUSCULUS, 'MUS_MUSCULUS'),
        (RATTUS_NORVEGICUS, 'RATTUS_NORVEGICUS')
    )


class Publication(models.Model):
    legacy_id = models.IntegerField()
    authors = models.TextField()
    title = models.CharField(max_length=255)
    journal = models.CharField(max_length=255)
    pages = models.CharField(max_length=15)
    date_sub = models.DateTimeField()
    doi = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    display = models.CharField(max_length=255)
    htmlid = models.CharField(max_length=255) # journal paper htmlid

    def get_primary_author(self):
        return self.authors.split(',')[0]

    def get_short_name(self):
        return '{} et al. {}'.format(self.authors.split(' ')[0], self.date_sub.strftime('%Y'))

    def get_submit_day(self):
        return self.date_sub.date()

    def get_model(self):
        model = self.dataset_set.all()
        if model:
            return self.dataset_set.all()[0].model
        else:
            return None

    def get_phenotype(self):
        model = self.dataset_set.all()
        if model:
            return self.dataset_set.all()[0].phenotype
        else:
            return None

    def get_paradigm(self):
        model = self.dataset_set.all()
        if model:
            return self.dataset_set.all()[0].paradigm
        else:
            return None

    def get_number_pub_genes(self):
        count = 0
        for ds in self.dataset_set.all():
            count += ds.get_number_genes()
        return count


class BrainRegion(models.Model):
    '''
    Some regions have special relationships to each other and can be grouped in searching.  We want to represent that
    here.  Only when "is_super_group" is checked would the grouped_regions matter.
    For example, if we have Amygdala can be Amygdala, Basolateral AMygdala, and Central Amygdala.
    '''

    name = models.CharField(unique=True, max_length=255)
    abbreviation = models.CharField(unique=True, max_length=255)



class Dataset(models.Model):
    TREATMENT_DID = "DID"
    TREATMENT_NONE = "NONE"
    TREATMENT_CIA = "CIA"
    TREATMENT_EOD = "EOD"
    TREATMENT_LPS = "LPS"

    TREATMENT_CHOICES = (
        (TREATMENT_DID, "DID"),
        (TREATMENT_NONE, "NONE"),
        (TREATMENT_CIA, "CIA"),
        (TREATMENT_EOD, "EOD"),
        (TREATMENT_LPS, "LPS"),
    )

    legacy_id = models.IntegerField()
    name = models.CharField(max_length=255, unique=True)
    treatment = models.CharField(max_length=255, choices=TREATMENT_CHOICES)
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    microarray = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    phenotype = models.CharField(max_length=255)
    species = models.CharField(max_length=255, choices=SpeciesType.SPECIES_CHOICES)
    brain_regions = models.ManyToManyField(BrainRegion, blank=True)  # treat like a tag.
    paradigm = models.CharField(max_length=255)
    paradigm_duration = models.CharField(max_length=255)
    alcohol = models.BooleanField()

    def get_number_genes(self):
        return self.iniagene_set.count()

    class Meta:
        ordering = ["name"]


class Homologene(models.Model):
    '''This is basically just a lookup table that is populated by NCBI Homologene Database:
    https://www.ncbi.nlm.nih.gov/homologene
    Items that share the same homlogene_group_id across species are homologenes.
    '''
    homologene_group_id = models.IntegerField(db_index=True)  # NCBI reference
    gene_symbol = models.CharField(db_index=True, max_length=255)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)
    species = models.CharField(choices=SpeciesType.SPECIES_CHOICES, max_length=255)
    brain = models.BooleanField()  # This is pre-determined by...
    ncbi_uid = models.IntegerField(db_index=True, unique=True)  # Not same as iniagene i guess?


class IniaGene(models.Model):  # Genes we do through experimentation
    '''IniaGenes are like data points that are collected from an experiment.  You use Homologene to convert across
    species for geneSymbol name.
    There can be multiple hologenes for the SAME species with the SAME group id.... those were CSVs in another app...

    '''

    DIRECTION_UP = "UP"
    DIRECTION_DOWN = "DOWN"

    DIRECTION_CHOICES = (
        (DIRECTION_UP, "UP"),
        (DIRECTION_DOWN, "DOWN")
    )


    legacy_id = models.IntegerField(db_index=True)  # From version 1.
    ncbi_uid = models.IntegerField(default=None, null=True)  # same as enterez id
    probe_id = models.CharField(max_length=255)  # Some kind of variable like LILMN_41111
    gene_symbol = models.CharField(db_index=True, max_length=255, blank=True)
    gene_name = models.CharField(max_length=255)
    p_value = models.FloatField(null=True, blank=True)  # stats
    fdr = models.FloatField()   # false discovery rate
    direction = models.CharField(max_length=255, choices=DIRECTION_CHOICES)
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT)
    homologenes = models.ManyToManyField(Homologene)
    updated = models.DateTimeField(auto_now=True)

    def list_human_orthologs(self):
        return ', '.join([h.gene_symbol for h in self.homologenes.all() if h.species == SpeciesType.HOMO_SAPIENS])

    def list_rat_orthologs(self):
        return ', '.join([h.gene_symbol for h in self.homologenes.all() if h.species == SpeciesType.RATTUS_NORVEGICUS])

    def list_mouse_orthologs(self):
        return ', '.join([h.gene_symbol for h in self.homologenes.all() if h.species == SpeciesType.MUS_MUSCULUS])

    def get_homologene_id(self):
        try:
            return self.homologenes.all()[0].homologene_group_id  # PREFETCHED!
        except:
            return None


class GeneAliases(models.Model):
    ''' This model contains the relationship between the allowed gene aliases per IniaGene.  No real hard checks here...
    allow pretty much whatever.
    '''
    symbol = models.CharField(max_length=255)
    IniaGene = models.ForeignKey(IniaGene, on_delete=models.CASCADE)


class SavedSearch(models.Model):
    search_parameters = JSONField()
