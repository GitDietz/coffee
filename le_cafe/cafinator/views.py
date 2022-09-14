import logging

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect

# from core.sendmail import send_text_email
from .forms import MemberForm, SetMeetingForm
from .models import Meetup, Member, MeetRecord
from .meeting import (create_meetings, loadconfig, update_meetup_list)

logger = logging.getLogger('coffee_log')


#  ####################  Member view ###################  #
def member_list(request):
    """
    Standard tabular listing of members
    :param request:
    :return: render template
    """
    logger.info('Start')
    objects = Member.objects.all()
    template = 'member_list.html'
    context = {
        'title': 'Member list',
        'objects': objects,
    }

    return render(request, template, context)


def member_new(request):
    """
    create a new member and create all permutations of meetings
    :param request:
    :return: render
    """
    template = 'member.html'
    logger.info('Start')
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            # branch off to create permutations if user is active
            if member.active:
                local_int_success, local_str_error, local_int_missed = update_meetup_list()
                if local_int_success == 0 and local_int_missed == 0:
                    messages.success(request, "Additional meetings added for the new member")
                else:
                    messages.error(request, "Meetup creation failed")
            return redirect('cafe:member_list')
        else:
            logger.error(f'Form: {form.errors}')
            messages.error(request, "Member creation failed")
    else:
        form = MemberForm()

    context = {
        'title': 'Add the member detail',
        'form': form,
    }
    return render(request, template, context)


def member_edit(request, pk):
    """
    update member detail or status
    Change in status will update the meeting permutation statuses
    :param request:
    :param pk: for the member
    :return: render
    """
    logger.debug('Start')
    template = 'member.html'
    try:
        member = Member.objects.get(pk=pk)

    except ObjectDoesNotExist:
        messages.error(request, "No such Member found")
        return redirect('cafe:member_list')

    form = MemberForm(request.POST or None, instance=member)
    if request.method == 'POST':
        # form = MemberForm(request.POST)
        if form.is_valid():
            member.save()
            if 'active' in form.changed_data:
                logger.debug('update meeting statuses')
                local_int_success, local_str_error, local_int_missed = update_meetup_list()
                if local_int_success == 0 and local_int_missed == 0:
                    messages.success(request, "Meetings altered for the updated member")
                else:
                    messages.error(request, "Meeting alteration failed")

            return redirect('cafe:member_list')
        else:
            logger.error(f'Form: {form.errors}')

    context = {
        'title': 'Edit the member detail',
        # 'object': member,
        'form': form,
    }
    return render(request, template, context)


#  ####################  Combinations ###################  #
def combination_list(request):
    """
    Display combinations of meetings and number of times utilised (arranged)
    :param request:
    :return: render
    """
    logger.info('Start')
    objects = Meetup.objects.all()

    template = 'combination_list.html'
    context = {
        'title': 'Meetup list',
        'objects': objects,
    }
    return render(request, template, context)


def meetup_list(request):
    """
    Displays the most recent 3 meeting sets that were arranged
    :param request:
    :return: render
    """
    logger.info('Start')
    objects = MeetRecord.objects.last_3()
    template = 'meetup_list.html'
    context = {
        'title': 'Meetups list',
        'objects': objects,
    }
    return render(request, template, context)


def get_latest_meeting_record():
    """
    returns information on the last meeting set
    :return: last_mtg names of people in last arranged meetings
    last_set - date when set
    """
    logger.info('Start')
    no_qs = False
    try:
        last_meeting = MeetRecord.objects.all().order_by('pk').last()
        if not last_meeting:
            no_qs = True
    except ObjectDoesNotExist:
        no_qs = True

    if no_qs:
        last_mtg = 'None'
        last_set = ''
    else:
        last_mtg = last_meeting.detail.strip()
        last_set = last_meeting.recorded
    return last_mtg, last_set


def make_email_body(in_str_meeting, in_bool_test):
    """
    Create the body of the email
    Parameters
    ----------
        in_str_meeting : combinations of meetings created
        in_bool_test : modifier to add test text
    Return
    ------
        body text

    """
    logger.info('Start')
    new_body = 'Good day, \n\n below is the list of meetings for the following 2 weeks:\n\n'
    logger.info(f'Meetings set: {in_str_meeting}')
    new_body += in_str_meeting + '\n\nMay your coffee be strong and your Mondays short,\n\n Pii Caffinator'
    if in_bool_test:
        new_body += '\n\n NB - this is only a test message'
    return new_body


def make_meetings(request):
    """
    The view to orchestrate the generation of a new set of meetings and then email it out
    """
    logger.info('Start')
    last_mtg, last_set = get_latest_meeting_record()

    form = SetMeetingForm()
    template = 'create_meeting.html'
    if request.method == "POST":
        if 'make_meeting' in request.POST:
            result = create_meetings()
            if result == 0:
                last_mtg, last_set = get_latest_meeting_record()
                messages.success(request, "New meeting set created")
            else:
                messages.success(request, "New meeting set failed")
            redirect('cafe:meetup_list')
        if 'email' in request.POST:
            local_int_success, local_dict_config = loadconfig()
            if local_int_success == 0:
                try:
                    local_str_body = make_email_body(last_mtg, False)
                    logger.error('Missing email functionality todo')
                    # send_text_email(local_dict_config.get('email_smtp'), local_dict_config.get('email_port'),
                    #                 local_dict_config.get('email_from'), local_dict_config.get('email_to'),
                    #                 local_dict_config.get('email_cc'), local_dict_config.get('email_subject'),
                    #                 local_str_body, None, None)
                    messages.success(request, "Email sent to the DL")
                except Exception as e:
                    logger.error(f'Email sending failed: {e}')
                    messages.error(request, 'Email not successfully sent')
            else:
                logger.error(f'Email config read failed')
                messages.error(request, 'Email config error')
            redirect('cafe:meetup_list')

    # with transaction.atomic():
    #    last_mtg, last_set = get_latest_meeting_record()
    context = {
        'title': 'Create new meetups list',
        'form': form,
        'meetings': last_mtg,
        'created': last_set,
    }
    # print(f'{context}')
    return render(request, template, context)


def meet_test(request):
    """
    Test function with a URL to do development with, Once feature is developed
    this will just redirect to home
    """
    logger.info('Start')
    return redirect('home')


def make_meetings_admin(request):
    """
    An administrative view to run the make permutations view.
    Can only be used after the table has been cleared
    """
    logger.info('Start')
    # returnval = make_permutations()
    return redirect('cafe:meetup_list')
