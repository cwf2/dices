from django import forms
from django.db.models import Max
from .models import CharacterInstance, Character, Author, Work, Speech, SpeechTag

# attribute lists for the drop downs
def get_char_name_choices():
    return [(c.name, c.name) for c in Character.objects.all()]

def get_inst_name_choices():
    return [(name, name) for name in sorted(set(inst.name for inst in CharacterInstance.objects.all()))]

def get_author_name_choices():
    return [(a.name, a.name) for a in Author.objects.all()]

def get_work_title_choices():
    return [(title, title) for title in sorted(set(w.title for w in Work.objects.all()))]
    
def get_work_lang_choices():
    return [("", "any")] + Work.Language.choices

#
# form classes
#

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
    # lazy field definitions
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["char_name"] = forms.MultipleChoiceField(
            label = "Name", 
            choices = get_char_name_choices(),
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["char_gender"] = forms.MultipleChoiceField(
            label = "Gender", 
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["char_being"] = forms.MultipleChoiceField(
            label = "Being", 
            choices = Character.CharacterBeing.choices, 
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["char_number"] = forms.ChoiceField(
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
    # lazy field definitions
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["inst_name"] = forms.MultipleChoiceField(
            label = "Name", 
            choices = get_inst_name_choices(),
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["inst_gender"] = forms.MultipleChoiceField(
            label = "Gender", 
            choices = Character.CharacterGender.choices, 
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["inst_being"] = forms.MultipleChoiceField(
            label = "Being", 
            choices = Character.CharacterBeing.choices, 
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["inst_number"] = forms.MultipleChoiceField(
            label = "Number",
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["inst_anon"] = forms.ChoiceField(
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
    # lazy field definitions
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.fields["lang"] = forms.ChoiceField(
            label = "Language",
            choices = get_work_lang_choices(), 
            required = False,
            initial = "",
            widget = forms.Select(attrs={
                "class": "form-select tagging-select",
                "data-allow-clear": "true",
                "data-minimum-results-for-search": "Infinity",            
            }),
        )
        self.fields["author_name"] = forms.MultipleChoiceField(
            label = "Author", 
            choices = get_author_name_choices(),
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["work_title"] = forms.MultipleChoiceField(
            label = "Work Title", 
            choices = get_work_title_choices(),
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )


class SpeechForm(forms.Form):
    # lazy field definitions
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        max_parts = Speech.objects.aggregate(Max("part"))["part__max"] or 1
        
        self.fields["type"] = forms.MultipleChoiceField(
            label = "Speech Type",
            choices = Speech.SpeechType.choices,
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["tags"] = forms.MultipleChoiceField(
            label = "Tags",
            choices = SpeechTag.TagType.choices,
            required = False,
            widget = forms.SelectMultiple(attrs={"class": "form-select tagging-select"}),
        )
        self.fields["part"] = forms.IntegerField(
            label = "Position in cluster",
            required = False,
            min_value = 1,
            max_value = max_parts,
            widget = forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
        )
        self.fields["n_parts"] = forms.IntegerField(
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
    
    # lazy field definitions
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["char_name"] = forms.MultipleChoiceField(
            choices = get_char_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["char_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["char_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["char_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["char_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["char_number"] = forms.ChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.HiddenInput(),
        )
    
        self.fields["inst_name"] = forms.MultipleChoiceField(
            choices = get_inst_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["inst_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["inst_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )        
        self.fields["inst_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["inst_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["inst_number"] = forms.MultipleChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["inst_anon"] = forms.ChoiceField(
            choices = [("True", "True"), ("False", "False")],
            required = False,
            widget = forms.HiddenInput(),
        )    
    
        self.fields["spkr_char_name"] = forms.MultipleChoiceField(
            choices = get_char_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_char_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["spkr_char_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )        
        self.fields["spkr_char_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_char_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_char_number"] = forms.ChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["spkr_inst_name"] = forms.MultipleChoiceField(
            choices = get_inst_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_inst_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["spkr_inst_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["spkr_inst_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_inst_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_inst_number"] = forms.MultipleChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["spkr_inst_anon"] = forms.ChoiceField(
            choices = [("True", "True"), ("False", "False")],
            required = False,
            widget = forms.HiddenInput(),
        )
            
        self.fields["addr_char_name"] = forms.MultipleChoiceField(
            choices = get_char_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_char_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["addr_char_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )        
        self.fields["addr_char_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_char_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_char_number"] = forms.ChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["addr_inst_name"] = forms.MultipleChoiceField(
            choices = get_inst_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_inst_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["addr_inst_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )        
        self.fields["addr_inst_gender"] = forms.MultipleChoiceField(
            choices = Character.CharacterGender.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_inst_being"] = forms.MultipleChoiceField(
            choices = Character.CharacterBeing.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_inst_number"] = forms.MultipleChoiceField(
            choices = Character.CharacterNumber.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["addr_inst_anon"] = forms.ChoiceField(
            choices = [("True", "True"), ("False", "False")],
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
    
        # work properties
        self.fields["lang"] = forms.ChoiceField(
            choices = get_work_lang_choices(),
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["author_name"] = forms.MultipleChoiceField(
            choices = get_author_name_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["author_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["author_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["work_pubid"] = forms.CharField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["work_id"] = forms.IntegerField(
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["work_title"] = forms.MultipleChoiceField(
            choices = get_work_title_choices(),
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
    
        self.fields["type"] = forms.MultipleChoiceField(
            choices = Speech.SpeechType.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["tags"] = forms.MultipleChoiceField(
            choices = SpeechTag.TagType.choices,
            required = False,
            widget = forms.MultipleHiddenInput(),
        )
        self.fields["part"] = forms.IntegerField(
            min_value = 1,
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["n_parts"] = forms.IntegerField(
            min_value = 1,
            required = False,
            widget = forms.HiddenInput(),
        )
        self.fields["level"] = forms.IntegerField(
            min_value = 0,
            required = False,
            widget = forms.HiddenInput(),
        )
    
        self.fields["page_size"] = forms.ChoiceField(
            choices = [("25", "25 per page"), ("50", "50 per page"), ("100", "100 per page"), ("0", "view all")],
            required = False,
            widget = forms.Select(attrs={
                "class": "btn btn-outline-secondary btn-small",
            }),
        )