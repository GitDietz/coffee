from django.urls import path, re_path

from .views import (combination_list, member_edit, member_list, member_new,
                    meet_test, make_meetings, meetup_list)

app_name = 'cafinator'

urlpatterns = [
    path('combination_list', combination_list, name='combination_list'),
    # path('make_permutations', make_permutations, name='make_permutations'),
    path('make_meetings', make_meetings, name='make_meetings'),
    path('meet_test', meet_test, name='meet_test'),
    path('meetup_list', meetup_list, name='meetup_list'),
    re_path('member/(?P<pk>\d+)', member_edit, name='member_edit'),
    path('member_list', member_list, name='member_list'),
    path('member_new', member_new, name='member_new'),
]
