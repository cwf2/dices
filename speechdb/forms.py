from django import forms
from django.db.models import Max
from .models import CharacterInstance, Character, Author, Work, Speech, SpeechTag

# attribute lists for the drop downs
char_name_choices = [(c.name, c.name) for c in Character.objects.all()]
inst_name_choices = [(name, name) for name in sorted(set(inst.name for inst in CharacterInstance.objects.all()))]
author_name_choices = [(a.name, a.name) for a in Author.objects.all()]
work_title_choices = [(title, title) for title in sorted(set(w.title for w in Work.objects.all()))]

class PrefixedForm(forms.Form):
    def add_prefix(self, field_name):
        # Use '_' instead of '-'
        if self.prefix:
            new_name = f"{self.prefix}_{field_name}"  
        else:
            new_name = field_name
        return new_name
        
    def clean(self):
        cleaned = super().clean()
        # leave prefixes in keys of cleaned data
        if self.prefix:
            prefixed_data = {f"{self.prefix}_{k}": v for k, v in cleaned.items()}
            return prefixed_data
        return cleaned


class CharacterForm(PrefixedForm):
    # field definitions
    char_name = forms.MultipleChoiceField(
        label = "Name", 
        choices = char_name_choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    char_gender = forms.MultipleChoiceField(
        label = "Gender", 
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    char_being = forms.MultipleChoiceField(
        label = "Being", 
        choices = Character.CharacterBeing.choices, 
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    char_number = forms.ChoiceField(
        label = "Number",
        choices = [("", "any")] + Character.CharacterNumber.choices,
        required = False,
        initial = "",
        widget = forms.Select(attrs={
            "class": "form-select tagging-select", 
            "data-allow-clear": "true",
            "data-minimum-results-for-search": "Infinity",
        }),
    )


class InstanceForm(PrefixedForm):
    # field definitions
    inst_name = forms.MultipleChoiceField(
        label = "Name", 
        choices = inst_name_choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    inst_gender = forms.MultipleChoiceField(
        label = "Gender", 
        choices = Character.CharacterGender.choices, 
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    inst_being = forms.MultipleChoiceField(
        label = "Being", 
        choices = Character.CharacterBeing.choices, 
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    inst_number = forms.MultipleChoiceField(
        label = "Number",
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    inst_anon = forms.ChoiceField(
        label = "Anon",
        choices = [("", "any"), ("True", "True"), ("False", "False")],
        required = False,
        initial = "",
        widget = forms.Select(attrs={
            "class": "form-select tagging-select", 
            "data-allow-clear": "true",
            "data-minimum-results-for-search": "Infinity",
        }),
    )
    
    

class TextForm(PrefixedForm):
    lang = forms.ChoiceField(
        label = "Language",
        choices = [("", "any")] + Work.Language.choices, 
        required = False,
        initial = "",
        widget = forms.Select(attrs={
            "class": "form-select tagging-select",
            "data-allow-clear": "true",
            "data-minimum-results-for-search": "Infinity",            
        }),
    )
    author_name = forms.MultipleChoiceField(
        label = "Author", 
        choices = author_name_choices, 
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    work_title = forms.MultipleChoiceField(
        label = "Work Title", 
        choices = work_title_choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    #work_id = forms.HiddenField()


class SpeechForm(forms.Form):
    max_parts = Speech.objects.aggregate(Max('part'))['part__max']
    
    type = forms.MultipleChoiceField(
        label = "Speech Type",
        choices = Speech.SpeechType.choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    tags = forms.MultipleChoiceField(
        label = "Tags",
        choices = SpeechTag.TagType.choices,
        required = False,
        widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
    )
    part = forms.IntegerField(
        label = "Position in cluster",
        required = False,
        min_value = 1,
        max_value = max_parts,
        widget = forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    n_parts = forms.IntegerField(
        label = "Parts in cluster",
        required = False,
        min_value = 1,
        max_value = max_parts,
        widget = forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    level = forms.IntegerField(
        label = "Embedded level",
        required = False,
        min_value = 0,
        widget = forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    
    
class PagerForm(forms.Form):
    char_name = forms.MultipleChoiceField(
        choices = char_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    char_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    char_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    char_number = forms.ChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.HiddenInput(),
    )
    
    inst_name = forms.MultipleChoiceField(
        choices = inst_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    inst_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    inst_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    inst_number = forms.MultipleChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    inst_anon = forms.ChoiceField(
        choices = [("True", "True"), ("False", "False")],
        required = False,
        widget = forms.HiddenInput(),
    )
    
    
    spkr_char_name = forms.MultipleChoiceField(
        choices = char_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_char_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_char_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_char_number = forms.ChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.HiddenInput(),
    )
    spkr_inst_name = forms.MultipleChoiceField(
        choices = inst_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_inst_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_inst_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_inst_number = forms.MultipleChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    spkr_inst_anon = forms.ChoiceField(
        choices = [("True", "True"), ("False", "False")],
        required = False,
        widget = forms.HiddenInput(),
    )
    
        
    addr_char_name = forms.MultipleChoiceField(
        choices = char_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_char_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_char_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_char_number = forms.ChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.HiddenInput(),
    )
    addr_inst_name = forms.MultipleChoiceField(
        choices = inst_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_inst_gender = forms.MultipleChoiceField(
        choices = Character.CharacterGender.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_inst_being = forms.MultipleChoiceField(
        choices = Character.CharacterBeing.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_inst_number = forms.MultipleChoiceField(
        choices = Character.CharacterNumber.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    addr_inst_anon = forms.ChoiceField(
        choices = [("True", "True"), ("False", "False")],
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    
    lang = forms.ChoiceField(
        required = False,
        widget = forms.HiddenInput(),
    )
    author_name = forms.MultipleChoiceField(
        choices = author_name_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    work_title = forms.MultipleChoiceField(
        choices = work_title_choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    
    type = forms.MultipleChoiceField(
        choices = Speech.SpeechType.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    tags = forms.MultipleChoiceField(
        choices = SpeechTag.TagType.choices,
        required = False,
        widget = forms.MultipleHiddenInput(),
    )
    part = forms.IntegerField(
        min_value = 1,
        required = False,
        widget = forms.HiddenInput(),
    )
    n_parts = forms.IntegerField(
        min_value = 1,
        required = False,
        widget = forms.HiddenInput(),
    )
    level = forms.IntegerField(
        min_value = 0,
        required = False,
        widget = forms.HiddenInput(),
    )
    
    page_size = forms.ChoiceField(
        choices = [("25", "25 per page"), ("50", "50 per page"), ("100", "100 per page"), ("0", "view all")],
        required = False,
        widget = forms.Select(attrs={
            "class": "btn btn-outline-secondary btn-small",
        }),
    )