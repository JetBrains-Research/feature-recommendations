import math

from util import _is_intersection


def compute_map_k(user_to_done, user_to_recommendation, K):
    user_cnt = 0
    map_k = 0
    for device_id in user_to_recommendation.keys():
        user_cnt += 1
        done_tips = user_to_done[device_id]
        recommended_tips = user_to_recommendation[device_id]
        ap_k = 0
        for j in range(min(len(recommended_tips), K)):
            if _is_intersection(done_tips, [recommended_tips[j]]):
                p_k = 0
                for k in range(j + 1):
                    if _is_intersection(done_tips, [recommended_tips[k]]):
                            p_k += 1
                p_k = p_k * 1. / (j + 1)
                ap_k += p_k
        ap_k = ap_k * 1. / K
        map_k += ap_k

    map_k = map_k * 1. / user_cnt * 10
    return map_k


def compute_ndcg_k(user_to_done, user_to_recommendation, K):
    ndcg_k = 0
    user_cnt = 0
    for device_id in user_to_recommendation.keys():
        user_cnt += 1
        done_tips = user_to_done[device_id]
        recommended_tips = user_to_recommendation[device_id]
        dcg_k = 0
        idcg_k = 0
        for j in range(min(len(recommended_tips), K)):
            idcg_k += 1. / math.log2(j + 2)
            if _is_intersection(done_tips, [recommended_tips[j]]):
                dcg_k += 1. / math.log2(j + 2)
        ndcg_k += dcg_k * 1. / idcg_k

    ndcg_k = ndcg_k * 1. / user_cnt
    return ndcg_k


def compute_accuracy_first(user_to_done, user_to_recommendation):
    prec = 0
    user_cnt = 0
    for device_id in user_to_recommendation.keys():
        user_cnt += 1
        done_tips = user_to_done[device_id]
        recommended_tips = user_to_recommendation[device_id]
        if _is_intersection(done_tips, [recommended_tips[0]]):
            prec += 1

    prec = prec * 1. / user_cnt
    return prec


def compute_mrr_k(user_to_done, user_to_recommendation, K):
    mrr_k = 0
    user_cnt = 0
    for device_id in user_to_recommendation.keys():
        user_cnt += 1
        done_tips = user_to_done[device_id]
        recommended_tips = user_to_recommendation[device_id]
        rr_k = 0
        for j in range(min(len(recommended_tips), K)):
            if _is_intersection(done_tips, [recommended_tips[j]]):
                rr_k = 1. / (j + 1)
                break
        mrr_k += rr_k

    mrr_k = mrr_k * 1. / user_cnt
    return mrr_k
