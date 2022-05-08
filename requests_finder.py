import re
import itertools

__all__ = ["load_request", "mention_pos", "contains_mention", "contains_mention_mp", "clip_sentence"]


whitespace = re.compile("[\s\u0020\u00a0\u1680\u180e\u202f\u205f\u3000\u2000-\u200a]+", re.UNICODE)

def squeeze_whitespace(input_):
    return whitespace.sub(" ", input_).strip()


def find_end_of_brakets(text: str, start_pos: int):
    """
    This function finds the end of the brackets in text given position of brackets' opening
    Returns position in the text of type integer.
    """
    try:
        if text[start_pos] != "(":
            return
    except Exception:
        return

    m = []
    for c in text:
        if c == "(":
            m.append(1)
        elif c == ")":
            m.append(-1)
        else:
            m.append(0)

    assert sum(m) == 0

    counter = 0
    for i in range(len(m[start_pos:])):
        counter += m[start_pos + i]
        if counter == 0:
            return start_pos + i + 1
            break
    return None


def find_biggest_entities(req):
    """
    This function finds biggest separate parts in one request. Works recursively.
    Returns list of biggest entities.
    Example: (me /1 you) or (me /1 (phone OR computer)) --> [[me, 1, you], [me, 1, [phone, computer]]]
    """
    biggest = []

    req = " ".join(req.split())
    words = req.split()

    curr = 0
    while curr < len(words):
        if words[curr][0] == "(":
            start = 0
            for c in range(curr):
                start += len(words[c]) + 1
            end = find_end_of_brakets(req, start)

            if words[curr - 1][0] == "/" or words[curr - 1] == "$AND$":
                biggest[-1].append(find_biggest_entities(req[start+1:end-1]))
            else:
                biggest.append(req[start:end])
                biggest[-1] = find_biggest_entities(biggest[-1][1:-1])

            curr += len(req[start:end].split())

        elif words[curr] == "$OR$":
            curr += 1

        elif words[curr] == "$AND$":
            if any([x == "$AND$" for x in biggest[-1]]):
                pass
            else:
                biggest[-1] = [biggest[-1]]

            if words[curr + 1][0] != "(":
                start = 0
                for c in range(curr + 1):
                    start += len(words[c]) + 1

                end = 0
                for c in range(curr + 2):
                    end += len(words[c]) + 1
                end -= 1

                biggest[-1].append(str(words[curr]))
                biggest[-1].append(req[start:end])
                curr += len(req[start-len(words[curr]) - 1:end].split())

            else:
                start = 0
                for c in range(curr):
                    start += len(words[c]) + 1
                end = start + len(words[curr]) + 1

                biggest[-1].append(str(words[curr]))
                curr += len(req[start:end].split())

        elif words[curr][0] == "/":
            if any([isinstance(x, int) for x in biggest[-1]]):
                pass
            else:
                biggest[-1] = [biggest[-1]]

            if words[curr + 1][0] != "(":
                start = 0
                for c in range(curr + 1):
                    start += len(words[c]) + 1

                end = 0
                for c in range(curr + 2):
                    end += len(words[c]) + 1
                end -= 1

                biggest[-1].append(int(words[curr][1:]))
                biggest[-1].append(req[start:end])
                curr += len(req[start-len(words[curr]) - 1:end].split())

            else:
                start = 0
                for c in range(curr):
                    start += len(words[c]) + 1
                end = start + len(words[curr]) + 1

                biggest[-1].append(int(words[curr][1:]))
                curr += len(req[start:end].split())
        else:
            biggest.append(words[curr])
            curr += 1

    return(biggest)

# def find_biggest_entities(req):
#     """
#     This function finds biggest separate parts in one request. Works recursively.
#     Returns list of biggest entities.
#     Example: (me /1 you) or (me /1 (phone OR computer)) --> [[me, 1, you], [me, 1, [phone, computer]]]
#     """
#     biggest = []
#
#     req = " ".join(req.split())
#     words = req.split()
#
#     curr = 0
#     while True:
#         if words[curr][0] == "(":
#             start = 0
#             for c in range(curr):
#                 start += len(words[c]) + 1
#             end = find_end_of_brakets(req, start)
#
#             if words[curr - 1][0] == "/":
#                 biggest[-1].append(find_biggest_entities(req[start+1:end-1]))
#             else:
#                 biggest.append(req[start:end])
#                 biggest[-1] = find_biggest_entities(biggest[-1][1:-1])
#
#             curr += len(req[start:end].split())
#
#         elif words[curr] == "OR":
#             curr += 1
#
#         elif words[curr] == "И":
#             curr += 1
#
#         elif words[curr][0] == "/":
#             biggest[-1] = [biggest[-1]]
#
#             if words[curr + 1][0] != "(":
#                 start = 0
#                 for c in range(curr + 1):
#                     start += len(words[c]) + 1
#
#                 end = 0
#                 for c in range(curr + 2):
#                     end += len(words[c]) + 1
#                 end -= 1
#
#                 biggest[-1].append(int(words[curr][1:]))
#                 biggest[-1].append(req[start:end])
#                 curr += len(req[start-len(words[curr]) - 1:end].split())
#
#             else:
#                 start = 0
#                 for c in range(curr):
#                     start += len(words[c]) + 1
#                 end = start + len(words[curr]) + 1
#
#                 biggest[-1].append(int(words[curr][1:]))
#                 curr += len(req[start:end].split())
#         else:
#             biggest.append(words[curr])
#             curr += 1
#
#         if curr >= len(words):
#             break
#
#     return(biggest)


def permutate(obj: list):
    #     if there are no sub-lists
    if not any([isinstance(x, list) for x in obj]):
        return list(itertools.permutations(obj))

    lists = []
    for elem in obj:
        if not isinstance(elem, list):
            lists.append([elem])
        else:
            lists.append(elem)

    out = []
    product = itertools.product(*lists)
    for p in product:
        out.extend(list(itertools.permutations(p)))

    return out


def unpack(main):
    """
    This function takes output from find_biggest_entities() and converts it to regexp string
    """
    if isinstance(main, list):
        pass
    else:
        return main
#     print("MAIN\t", main)
    processed = []

    for sub in main:
        #         print("sub --", sub)
        if isinstance(sub, list):
            processed.append(unpack(sub))
        else:
            if isinstance(sub, str):
                if sub == "$AND$":
                    processed.append(sub)
                    continue
                if "*" not in sub:
                    processed.append(r"\b" + sub + r"\b")
                else:
                    processed.append(r"\b" + sub)
            else:
                processed.append(sub)
#     print("processed --", processed)

    out = []
    indxs_int = [i for i, x in enumerate(processed) if isinstance(x, int)]
    indxs_int.extend([i for i, x in enumerate(processed) if x == "$AND$"])
    indxs_other = [i for i, x in enumerate(processed) if i not in indxs_int]
#     return processed, indxs_int
    if indxs_int == []:
        #         print("No integers")
        #         print("Out --", processed)
        for i in indxs_other:
            if isinstance(processed[i], list):
                for w in processed[i]:
                    out.append(w)
            else:
                out.append(processed[i])
#         print("Main --", main, "-- Out --", out)
        return out
    else:
        if not any([isinstance(processed[x], int) for x in indxs_int]):
            sep = ".{1,1000}"
            indexes_to_permutate = []
            for i in indxs_int:
                if i - 1 in indxs_other and i - 1 not in indexes_to_permutate:
                    indexes_to_permutate.append(i - 1)
                if i + 1 in indxs_other and i + 1 not in indexes_to_permutate:
                    indexes_to_permutate.append(i + 1)

            for combination in permutate([processed[j] for j in indexes_to_permutate]):
                #                 print(combination)
                combination_regexp = ""
                for n, word in enumerate(combination):
                    combination_regexp += word
                    if n + 1 != len(combination):
                        combination_regexp += sep
                out.append(combination_regexp)
        else:
            for i in indxs_int:
                if processed[i] == "$AND$":
                    sep = ".{1,1000}"
                else:
                    sep = ".{1,%s}" % processed[i]

                if i + 1 in indxs_other and i - 1 in indxs_other:
                    left = processed[i-1]
                    if not isinstance(left, list):
                        left = [left]
                    right = processed[i+1]
                    if not isinstance(right, list):
                        right = [right]
                    product = itertools.product(left, right)
                    for pair in product:
                        out.append(pair[0] + sep + pair[1])
                        out.append(pair[1] + sep + pair[0])

        for i in indxs_other:
            if (i + 1 not in indxs_int) and (i - 1 not in indxs_int):
                out.append(processed[i])

#     print("Main --", main, "-- Out --", out)
    return out
#
# def unpack(main):
#     """
#     This function takes output from find_biggest_entities() and converts it to regexp string
#     """
#     if isinstance(main, list):
#         pass
#     else:
#         return main
# #     print("MAIN\t", main)
#     processed = []
#
#     for sub in main:
#         #         print("sub --", sub)
#         if isinstance(sub, list):
#             processed.append(unpack(sub))
#         else:
#             if isinstance(sub, str):
#                 if "*" not in sub:
#                     processed.append(r"\b" + sub + r"\b")
#                 else:
#                     processed.append(r"\b" + sub)
#             else:
#                 processed.append(sub)
# #             processed.append(sub)
# #     print("processed --", processed)
#
#     out = []
#     indxs_int = [i for i, x in enumerate(processed) if isinstance(x, int)]
#     indxs_other = [i for i, x in enumerate(processed) if not isinstance(x, int)]
#     if indxs_int == []:
#         #         print("No integers")
#         #         print("Out --", processed)
#         for i in indxs_other:
#             if isinstance(processed[i], list):
#                 for w in processed[i]:
#                     #                     out += w + "|"
#                     #                     if "*" not in w:
#                     #                         out.append(r"^%s$" % w)
#                     #                     else:
#                     #                         out.append(r"^%s" % w)
#                     out.append(w)
#             else:
#                 #                 out += processed[i] + "|"
#                 out.append(processed[i])
# #         print("Main --", main, "-- Out --", out)
#         return out
#     else:
#         for i in indxs_int:
#             sep = ".{1,%s}" % str(processed[i])
#
#             if i + 1 in indxs_other and i - 1 in indxs_other:
#
#                 left = processed[i-1]
#                 if not isinstance(left, list):
#                     left = [left]
#                 right = processed[i+1]
#                 if not isinstance(right, list):
#                     right = [right]
#                 product = itertools.product(left, right)
#                 for pair in product:
#                     out.append(pair[0] + sep + pair[1])
# #                     out += pair[0] + sep + pair[1] + "|"
#                     out.append(pair[1] + sep + pair[0])
# #                     out += pair[1] + sep + pair[0] + "|"
#
#         for i in indxs_other:
#             if (i + 1 not in indxs_int) and (i - 1 not in indxs_int):
#                 #                 out += processed[i] + "|"
#                 out.append(processed[i])
#
# #     print("Main --", main, "-- Out --", out)
#     return out


def process_phrases(request):
    """replaces whitespaces in brackets (" ") with _ ("_")"""
    count = 0
    pred_i = -1
    for i in range(len(request)):
        c = request[i]
        if c == '\"':
            count = (count + 1) % 2
            if count == 1:
                pred_i = i

        if pred_i != -1 and count == 0:
            part = request[pred_i:i]
    #         print(part)
            part = part.replace(" ", "_")
            request = request[:pred_i] + part + request[i:]

            pred_i = -1
    request = request.replace('\"', "")
    return request


def load_request(fname=None, request=None):
    """
    This function loads request, precesses it and returns regexp string of it
    """
    if request is None:
        with open(fname, "r", encoding="utf8") as f:
            request = f.readlines()[0]

    request = request.replace(" И НЕ ", " $NOT$ ")
    request = request.replace(" NOT ", " $NOT$ ")
    request = request.replace(" и ", " $AND$ ")
    request = request.replace(" and ", " $AND$ ")
    request = request.replace(" AND ", " $AND$ ")
    request = request.replace(" И ", " $AND$ ")
    request = request.replace(" или ", " $OR$ ")
    request = request.replace(" ИЛИ ", " $OR$ ")
    request = request.replace(" or ", " $OR$ ")
    request = request.replace(" OR ", " $OR$ ")
    request = request.replace("/", " /")
    request = " ".join(request.split())

    # if there were some words to exclude, we process them separately and then combine in one lookahead regexp
    if " $NOT$ " in request:
        request_exclude = request[request.find(" $NOT$ "):]
        request_exclude = request_exclude.replace(" $NOT$ ", "")
        request = request[:request.find(" $NOT$ ")]
    else:
        request_exclude = None

    request = process_phrases(request)
    if request_exclude:
        # TODO: fix bug where ""NOT (papa)" results in ^(?!.*\bpapa*.*).* instead of ^(?!.*\bpapa\w*.*).*
        request_exclude = process_phrases(request_exclude)

    final = unpack(find_biggest_entities(request))
    if request_exclude:
        final_exclude = unpack(find_biggest_entities(request_exclude))
    else:
        final_exclude = []

    regexp_exclude = ""
    for s in final_exclude:
        if isinstance(s, list):
            regexp_exclude += s[0]
        elif isinstance(s, str):
            regexp_exclude += s + ".*|.*"

    if len(regexp_exclude) != 0:
        regexp_exclude = "^(?!.*" + regexp_exclude
        regexp_exclude = regexp_exclude[:-3]
        regexp_exclude = regexp_exclude.replace("_", r"\s")
        regexp_exclude += ").*"

    regexp = "("
    for s in final:
        if isinstance(s, list):
            regexp += s[0]
        elif isinstance(s, str):
            regexp += s + "|"
    regexp = regexp[:-1]
    regexp += ")"
    regexp = regexp.replace("_", r"\s")
    regexp = regexp.replace("*", r"\w*")

    if len(regexp_exclude) != 0:
        regexp = regexp_exclude + regexp + ".*$"

    return regexp


def mention_pos(text, request):
    """
    Function searches for mentions in the text based on tags
    text: parameter takes sentence
    request: path to the file with tags
    """
    try:
        return [m.span() for m in re.finditer(r"{}".format(request.lower()), text.lower())][0]
    except Exception:
        return None


def contains_mention(text, request):
    """
    Function checks if there is a mention of tags in the text
    """
    if re.findall(request.lower(), text.lower()) == []:
        return False
    else:
        return True


def contains_mention_mp(key2text, request):
    """
    Function checks if there is a mention of tags in the text

    USED FOR MULTIPROCESSING

    Args:
        key2text (tuple): (key, text)
    """
    if re.findall(request.lower(), key2text[1].lower()) == []:
        return (key2text[0], False)
    else:
        return (key2text[0], True)


def clip_sentence(text, request, n_sentences=2):
    """
    Function trims the text that is not mentioned by the tag
    """
    params = mention_pos(text, request)  # occurrence of words
    if params is not None:  # load_request from utils.py
        # before = list(filter(None, [text.strip(' ') for text in re.split("r[\w]+|[.!?;]", text[:params[0]])]))
        before = list(filter(None, [text.strip(' ') for text in re.split(r"[.!?;]+", text[:params[0]])]))
        mention = text[params[0]:params[1]]
        # wtf is "r[\w]+|[.!?;]" ?????????
        # after = list(filter(None, [text.strip(' ') for text in re.split("r[\w]+|[.!?;]", text[params[1]:])]))
        after = list(filter(None, [text.strip(' ') for text in re.split(r"[.!?;]+", text[params[1]:])]))
        x = '. '.join(before[-n_sentences:])+'. '+''.join(mention)+'. '+'. '.join(after[:n_sentences])

        if len(x) > 2000:
            x = x[:2000]

        return squeeze_whitespace(x)
    else:
        splitted_sentences = re.split(r"[.!?;]+", text)
        x = ""
        for n, sentence in enumerate(splitted_sentences):
            total_length = len(x) + len(sentence)
            if (total_length > 2000 and len(x) != 0) or ((n + 1) > (n_sentences * 2)):
                break
            else:
                x += sentence + ". "

        return squeeze_whitespace(x)
