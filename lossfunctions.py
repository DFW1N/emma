# ----------------------------------------------------
# Electromagnetic Mining Array (EMMA)
# Copyright 2018, Pieter Robyns
# ----------------------------------------------------

import keras.backend as K
import tensorflow as tf
from registry import lossfunctions, lossfunction


def get_loss(key_low, key_high, loss_type='correlation'):
    f = lossfunctions[loss_type]
    return f(key_low, key_high)


@lossfunction('correlation')
def _get_correlation_loss(key_low, key_high):
    def correlation_loss(y_true_raw, y_pred_raw):
        """
        Custom loss function that calculates the Pearson correlation of the prediction with
        the true values over a number of batches.
        """
        # y_true_raw = K.print_tensor(y_true_raw, message='y_true_raw = ')  # Note: print truncating is incorrect in the print_tensor function
        # y_pred_raw = K.print_tensor(y_pred_raw, message='y_pred_raw = ')
        y_true = (y_true_raw - K.mean(y_true_raw, axis=0, keepdims=True))  # We are taking correlation over columns, so normalize columns
        y_pred = (y_pred_raw - K.mean(y_pred_raw, axis=0, keepdims=True))

        loss = K.variable(0.0)
        for key_col in range(key_low, key_high):  # 0 - 16
            y_key = K.expand_dims(y_true[:, key_col], axis=1)  # [?, 16] -> [?, 1]
            y_keypred = K.expand_dims(y_pred[:, key_col - key_low], axis=1)  # [?, 16] -> [?, 1]
            denom = K.sqrt(K.dot(K.transpose(y_keypred), y_keypred)) * K.sqrt(K.dot(K.transpose(y_key), y_key))
            denom = K.maximum(denom, K.epsilon())
            correlation = K.dot(K.transpose(y_key), y_keypred) / denom
            loss += 1.0 - correlation

        return loss

    return correlation_loss


@lossfunction('correlation_special')
def _get_special_correlation_loss(key_low, key_high):
    def correlation_loss(y_true_raw, y_pred_raw):
        """
        Custom loss function that calculates the Pearson correlation of the prediction with
        the true values over a number of batches, with the addition of a weight parameter that
        is used to approximate the true key byte value.
        """
        y_true = (y_true_raw - K.mean(y_true_raw, axis=0, keepdims=True))  # We are taking correlation over columns, so normalize columns
        y_pred = (y_pred_raw - K.mean(y_pred_raw, axis=0, keepdims=True))
        weight_index = key_high - key_low

        loss = K.variable(0.0)
        weight = K.mean(y_pred_raw[:, weight_index], axis=0)
        for key_col in range(key_low, key_high):  # 0 - 16
            y_key = K.expand_dims(y_true[:, key_col], axis=1)  # [?, 16] -> [?, 1]
            y_keypred = K.expand_dims(y_pred[:, key_col - key_low], axis=1)  # [?, 16] -> [?, 1]
            denom = K.sqrt(K.dot(K.transpose(y_keypred), y_keypred)) * K.sqrt(K.dot(K.transpose(y_key), y_key))
            denom = K.maximum(denom, K.epsilon())
            correlation = K.dot(K.transpose(y_key), y_keypred) / denom
            loss += 1.0 - correlation

            alpha = 0.001
            exact_pwr = tf.multiply(weight, y_pred_raw[:, key_col - key_low])
            loss += alpha * K.sum(K.square(y_true_raw[:, key_col] - exact_pwr))

        return loss

    return correlation_loss


@lossfunction('abs_distance')
def _get_abs_distance_loss(key_low, key_high):
    return __get_distance_loss(key_low, key_high, False)


@lossfunction('squared_distance')
def _get_squared_distance_loss(key_low, key_high):
    return __get_distance_loss(key_low, key_high, True)


def __get_distance_loss(key_low, key_high, squared):
    def distance_loss(y_true_raw, y_pred_raw):
        y_true = y_true_raw
        y_pred = y_pred_raw

        loss = K.variable(0.0)
        for key_col in range(key_low, key_high):  # 0 - 16
            y_key = y_true[:, key_col]  # [?, 16] -> [?,]
            y_keypred = y_pred[:, key_col - key_low]  # [?, 16] -> [?,]
            if squared:
                loss += K.sum(K.square(y_key - y_keypred))
            else:
                loss += K.sum(K.abs(y_key - y_keypred))

        return loss

    return distance_loss


@lossfunction('crossentropy')
def _get_crossentropy_loss(*_):
    def crossentropy_loss(y_true, y_pred):
        return tf.nn.softmax_cross_entropy_with_logits(labels=y_true, logits=y_pred)
    return crossentropy_loss
