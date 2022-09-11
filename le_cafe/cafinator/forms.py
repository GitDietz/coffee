from django import forms

from .models import Meetup, Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = '__all__'


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meetup
        fields = '__all__'


class SetMeetingForm(forms.Form):
    meetings = forms.CharField(widget=forms.Textarea(attrs={'rows': 8, "cols": 30}), required=False, strip=True)
    created = forms.DateField(required=False)
