import logging
import random
from django.db import connection

from .models import Meetup, Member, MeetRecord, Reference

logger = logging.getLogger('coffee_log')


def fix_combination_detail():
    """
    Retrospectively add the detail names to the model. Should not be required in future
    Admin function to update the Meetup data (combination of who's meeting who) with actual names
    and not just the primary keys referring to the members
    eg. 1|2 adding Jack|Jill in a secondary column

    Parameters
    ==========
    None
    Returns
    =======
    local_int_success - pass or fail
    """
    logger.info('Start')
    local_int_success = 1
    objects = Meetup.objects.all()
    members = list(Member.objects.values_list('id', 'full_name'))
    dict_members = {key: value for key, value in members}
    try:
        for obj in objects:
            combo = str(obj.combination)
            parts = combo.split('|')
            person_1 = dict_members.get(int(parts[0]))
            person_2 = dict_members.get(int(parts[1]))
            detail_names = person_1 + ' | ' + person_2
            obj.named = detail_names
            obj.save()

        local_int_success = 0
    except Exception as e:
        logger.error(f'Encountered {e}')
    finally:
        logger.info('END')
        return local_int_success


def add_meetings(in_lis_mtg):
    """
    Creates all possible combinations of meetings between all members listed
    Has no exclusions for existing combinations or inactive members
    Was good for a start but little to no value as from Mar 21

    Parameters
    ==========
    in_lis_mtg : meetings list
    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    """
    logger.info('Start')
    local_int_success = 1
    local_str_error = ''
    local_int_target = len(in_lis_mtg)
    local_int_actual = 0
    try:
        members = list(Member.objects.values_list('id', 'full_name'))
        dict_members = {key: value for key, value in members}
        for perm in in_lis_mtg:
            combo = str(perm)
            parts = combo.split('|')
            person_1 = dict_members.get(int(parts[0]))
            person_2 = dict_members.get(int(parts[1]))
            detail_names = person_1 + ' | ' + person_2
            Meetup.objects.create(combination=perm, active=True, named=detail_names)
            local_int_actual += 1
        local_int_success = 0
    except Exception as e:
        logger.error(f'Encountered {e}')
        local_str_error = f'{e}'
    finally:
        local_int_incomplete = local_int_target - local_int_actual
        logger.info('END')
        return local_int_success, local_str_error, local_int_incomplete


def make_permutations_all_new():
    """
    using only active members create the permutations of meetings
    Only for use with a blank canvas with no pre-existing meetings
    @30/3/21 untested due to amendment of the method below to
    """
    logger.info('Start')
    members = list(Member.objects.values_list('id', 'full_name'))
    dict_members = {key: value for key, value in members}
    member_ids = list(Member.objects.active().order_by('id').values_list('id', flat=True))
    permutations = []
    while len(member_ids) > 1:
        for m in member_ids[1:]:
            permutations.append(str(member_ids[0]) + '|' + str(m))
        member_ids.pop(0)

    # now create this into the object Meetup
    for perm in permutations:
        combo = str(perm)
        parts = combo.split('|')
        person_1 = dict_members.get(int(parts[0]))
        person_2 = dict_members.get(int(parts[1]))
        detail_names = person_1 + ' | ' + person_2
        Meetup.objects.create(combination=perm, active=True, named=detail_names)

    new_objects = Meetup.objects.count()
    logger.info(f'Meetups created {new_objects}')
    return permutations


def get_meetings(in_str_set):
    """
    Function to return the queryset of meetup list selected based on the input value

    Parameters
    ==========
    in_str_set - choice of dataset

    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    meetings - list of tuple
    """
    logger.info('Start')
    local_int_success = 1
    local_str_error = ''
    try:
        if in_str_set == 'all':
            meetings = list(Meetup.objects.all().values_list('combination', 'active'))
        elif in_str_set == 'active':
            meetings = list(Meetup.objects.active().values_list('combination', 'active'))
        else:
            meetings = None
        local_int_success = 0
    except Exception as e:
        logger.error(f'Encountered {e}')
        local_str_error = f'{e}'
    finally:
        logger.info('END')
        # return local_int_success, local_str_error
        # TODO refactor return
        return meetings


def make_meeting_combinations():
    """
    using only active members create the permutations of meetings
    this will be used to either make meetup records, set them as active or inactive
    Parameters
    ==========
    None
    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    local_lis_permutations - all permutations of meetings for active members ('3|5')
    """
    logger.info('Start')
    local_int_success = 1
    local_str_error = ''
    try:
        # members = list(Member.objects.values_list('id', 'full_name'))
        # dict_members = {key: value for key, value in members}
        member_ids = list(Member.objects.active().order_by('id').values_list('id', flat=True))
        permutations = []
        while len(member_ids) > 1:
            for m in member_ids[1:]:
                permutations.append(str(member_ids[0]) + '|' + str(m))
            member_ids.pop(0)

        local_int_success = 0
    except Exception as e:
        logger.error(f'Encountered {e}')
        local_str_error = f'{e}'

    finally:
        logger.info('END')
        # return local_int_success, local_str_error TODO
        return permutations


def update_meetup_list():
    """
    Function to be called each time a team member is added, removed or made inactive
    This will then add/remove/deactivate the meetings associated with the member
    Parameters
    ==========
    None
    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    """
    logger.info('Start')
    local_int_success = 1
    local_str_error = ''
    local_int_missed = 0
    try:
        current_meetings = get_meetings('all')  # [('1|2', True),]
        active_member_combos = make_meeting_combinations()  # ['1|2',]
        for meeting in current_meetings:
            if (meeting[0] in active_member_combos) and meeting[1]:
                # active meeting found, remove it from the list, items remaining will be new or inactive
                active_member_combos.remove(meeting[0])
            elif (meeting[0] in active_member_combos) and not meeting[1]:
                local_obj_meeting = Meetup.objects.get(combination=meeting[0])
                local_obj_meeting.active = True
                local_obj_meeting.save()
                active_member_combos.remove(meeting[0])
            elif meeting[0] not in active_member_combos:
                # as above but set to inactive
                local_obj_meeting = Meetup.objects.get(combination=meeting[0])
                local_obj_meeting.active = False
                local_obj_meeting.save()
                logger.info(f'Meeting {meeting[0]} can not be active any more, updated')
            else:
                logger.warning(f'Meetup {meeting[0]} conditions are unusual: {meeting[1]}')

        logger.info(f'remaining meetings to add {len(active_member_combos)}')
        if len(active_member_combos) > 0:
            local_int_success, local_str_error, local_int_missed = add_meetings(active_member_combos)
        else:
            local_int_missed = 0
        local_int_success = 0
    except Exception as e:
        logger.error(f'Encountered {e}')
        local_str_error = f'{e}'
    finally:

        logger.info('END')
        return local_int_success, local_str_error, local_int_missed


def record_meetup(in_lis_meeting_names):
    """
    Write the meetup record to the database
    Parameters
    ==========
    in_lis_meeting_names e.g. Jan meets Kim
    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    """
    logger.info('Start')
    local_int_success = 1
    local_str_error = ''
    combined = ''
    try:
        for item in in_lis_meeting_names:
            combined += item + '\n'
        combined = combined.strip()
        MeetRecord.objects.create(detail=combined)
        local_int_success = 0
    except Exception as e:
        local_str_error = f'{e}'
    finally:
        return local_int_success, local_str_error


def update_meetings(in_lis_mtg):
    """
    go update the meeting table with the meetings selected to keep track of
    unique meeting combinations - avoids the same people meeting again until
    all combinations have been used
    Parameters
    ==========
    in_lis_mtg in the form of ['2|4','8|12']
    Returns
    =======
    local_int_success - pass or fail
    local_str_error - error generated internally
    """
    logger.info("Start")
    local_int_success = 1
    local_str_error = ''
    meetings_names = []
    try:
        for item in in_lis_mtg:
            ppl = item.split('|')
            person_1 = Member.objects.get(pk=int(ppl[0])).full_name
            person_2 = Member.objects.get(pk=int(ppl[1])).full_name
            meetings_names.append(person_1 + ' meeting ' + person_2)
            item_model = Meetup.objects.get(combination=item)
            item_model.increment()

        local_int_success = 0
    except Exception as e:
        logger.error(f'Error is {e}')
        local_str_error = f'{e}'
    finally:
        logger.info('END')
        return local_int_success, local_str_error, meetings_names


def get_db_value(in_sql_str, in_out_format_str):
    """
    Get a single value return from the DB, will fail if a set is returned
    :param in_sql_str: the raw query
    :param in_out_format_str: how the item should be returned
    :return:
    """
    logger.info('Start')
    try:
        with connection.cursor() as cursor:
            cursor.execute(in_sql_str)
            result = cursor.fetchone()[0]
        if in_out_format_str == 'str':
            return str(result)
        elif in_out_format_str == 'int':
            return int(result)
        else:
            return result
    except Exception as e:
        logger.error(f'Issue found {e}')
        return None


def get_unique_pairs(in_lis_mtg, in_lis_members):
    """
    To find the first unique sets of meetings taking the items as they are in order
    Has application when there are a small number of options
    :param in_lis_mtg:
    :param in_lis_members:
    :return:
    """
    logger.info('Start')
    unique = []
    members = in_lis_members
    random.shuffle(in_lis_mtg)
    for mtg in in_lis_mtg:
        mtg_member = mtg.split('|')
        if mtg_member[0] not in members and mtg_member[1] not in members:
            members.append(mtg_member[0])
            members.append(mtg_member[1])
            unique.append(mtg)
    return unique, members


def get_random_pairs(in_lst_choices, in_int_selections, in_lst_already_chosen):
    """
    makes random selections from the available sets,
    checking that the members have not been set up for a meeting before
    in_lst_choices : pairs to pick from
    in_int_selections: number of combinations to add
    in_lst_already_chosen : combination pairs already selected
    """
    logger.info('Start')
    combinations = in_lst_already_chosen
    permutations = in_lst_choices
    individuals = get_individuals(in_lst_already_chosen)
    unique_pairs, all_individuals = get_unique_pairs(permutations, individuals)
    if len(unique_pairs) <= in_int_selections:
        logger.info('small set of pairs available')
        return 0, unique_pairs, all_individuals
    else:
        new_ppl = []
        while len(combinations) < in_int_selections:
            pick = random.choice(permutations)
            new_ppl = pick.split('|')
            if new_ppl[0] not in individuals and new_ppl[1] not in individuals:
                individuals.append(new_ppl[0])
                individuals.append(new_ppl[1])
                combinations.append(pick)
        return 0, combinations, individuals


def get_individuals(in_lst_combinations):
    logger.info('Start')
    individuals = []
    for pair in in_lst_combinations:
        members = pair.split('|')
        individuals.append(members[0])
        individuals.append(members[1])
    return individuals


def get_mtg_combinations(in_qs_mtg):
    """
    Extracts meeting combinations and the combination primary key from queryset
    parameters
    ==========
    in_qs_mtg queryset of meetings

    Outputs
    =======
    local_int_success int 0/1
    meeting_combinations list
    meeting_pks list
    """
    logger.info('Start')
    local_int_success = 1
    meeting_combinations = []
    meeting_pks = []
    try:
        for item in in_qs_mtg:
            meeting_combinations.append(item.combination)
            meeting_pks.append(item.pk)
        local_int_success = 0
    except Exception as e:
        print(f'Error: {e}')
    finally:
        return local_int_success, meeting_combinations, meeting_pks


def create_meetings():
    """
    Managed the creation of meetings based on the number of members there are
    Completes by creating the set record in the database table

    Outputs
    =======
    local_int_success : 0/1 success or failure
    """
    logger.info('Start')
    planned_mtgs = []  # to be a list of strings that represent pks for the members
    selected_mtg_keys = []
    selected_member_keys = []
    # local_lis_mtgs looks like this  ['12|15', '2|16', '11|14', '5|9', '7|13', '3|8', '4|6']
    try:
        meetings_required = Member.meetings_to_set()
        meetings_set = 0
        i = 0
        local_lis_individuals = []
        while meetings_required > meetings_set:
            meetings_now_reqd = meetings_required - meetings_set
            least_allocated = get_db_value('SELECT min(meetings) FROM coffee_meetup WHERE active = 1', 'int') + i
            qs_first_pool = Meetup.objects.done_times(least_allocated)
            local_int_success, local_list_pool_pairs, pool_mtg_keys = get_mtg_combinations(qs_first_pool)
            local_int_success, local_lis_mtgs, local_lis_individuals = get_random_pairs(local_list_pool_pairs,
                                                                                        meetings_now_reqd,
                                                                                       planned_mtgs)
            planned_mtgs.extend(local_lis_mtgs)
            meetings_found = len(planned_mtgs)
            meetings_set += meetings_found
            i += 1

        logger.info(f'meetings found {planned_mtgs}, all up {meetings_found}')
        local_int_success, local_str_error, local_lst_meetings = update_meetings(planned_mtgs)
        local_int_success, local_str_error = record_meetup(local_lst_meetings)
    except Exception as e:
        local_int_success = 1
        logger.error(f'Error in test : {e}')
    finally:
        # assuming we have enough meetings
        logger.info(f'The following people are meeting: {local_lst_meetings}')
        return local_int_success


def loadconfig():
    """
    Load the config values from the DB table
    parameters
    ==========
    none
    Returns
    =======
    local_int_success int 0/1
    local_dict_config dict with the config elements
    """
    logger.info('Load config start')
    local_int_success = 1
    local_dict_config = {}
    try:
        local_dict_config['email_smtp'] = Reference.objects.get(name='email_smtp').ref_str
        local_dict_config['email_port'] = Reference.objects.get(name='email_port').ref_int
        local_dict_config['email_from'] = Reference.objects.get(name='email_from').ref_str
        local_dict_config['email_cc'] = Reference.objects.get(name='email_cc').ref_str
        local_dict_config['email_subject'] = Reference.objects.get(name='email_subject').ref_str
        local_dict_config['email_to'] = Reference.objects.get(name='email_to').ref_str
        local_int_success = 0
    except Exception as e:
        local_str_error = f'Validation failed {e}'
        logger.error(local_str_error)
    finally:
        logger.info('Config complete')
        return local_int_success, local_dict_config
