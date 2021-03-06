# -*- coding: UTF-8 -*-
import re
from fastText import train_supervised
import tensorflow as tf
from . import mode_site

'''
    fastText
'''
def fasttext(input,epoch=25,wordNgrams=2):
    
    model = train_supervised(
        input=input,
        epoch=epoch, lr=0.9, wordNgrams=wordNgrams, verbose=2, minCount=1)
    return model


'''
TextCNN    
'''

def TextCNN(config):
    """文本分类，CNN模型"""
    if config == '':
        config = mode_site.TCNNConfig
    # 三个待输入的数据
    input_x = tf.placeholder(tf.int32, [None, config.seq_length], name='input_x')
    input_y = tf.placeholder(tf.float32, [None, config.num_classes], name='input_y')
    keep_prob = tf.placeholder(tf.float32, name='keep_prob')

    """CNN模型"""
    # 词向量映射
    with tf.device('/cpu:0'):
        embedding = tf.get_variable('embedding', [config.vocab_size, config.embedding_dim])
        embedding_inputs = tf.nn.embedding_lookup(embedding, input_x)

    with tf.name_scope("cnn"):
        # CNN layer
        conv = tf.layers.conv1d(embedding_inputs, config.num_filters, config.kernel_size, name='conv')
        # global max pooling layer
        gmp = tf.reduce_max(conv, reduction_indices=[1], name='gmp')

    with tf.name_scope("score"):
        # 全连接层，后面接dropout以及relu激活
        fc = tf.layers.dense(gmp, config.hidden_dim, name='fc1')
        fc = tf.contrib.layers.dropout(fc, keep_prob)
        fc = tf.nn.relu(fc)

        # 分类器
        logits = tf.layers.dense(fc, config.num_classes, name='fc2')
        y_pred_cls = tf.argmax(tf.nn.softmax(logits), 1)  # 预测类别

    with tf.name_scope("optimize"):
        # 损失函数，交叉熵
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=input_y)
        loss = tf.reduce_mean(cross_entropy)
        # 优化器
        optim = tf.train.AdamOptimizer(learning_rate=config.learning_rate).minimize(loss)

    with tf.name_scope("accuracy"):
        # 准确率
        correct_pred = tf.equal(tf.argmax(input_y, 1), y_pred_cls)
        acc = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    return optim,acc

'''
    TextRNN
'''
def TextRNN(config):
    """文本分类，RNN模型"""
    if config == '':
        config = mode_site.TRNNConfig

    # 三个待输入的数据
    input_x = tf.placeholder(tf.int32, [None, config.seq_length], name='input_x')
    input_y = tf.placeholder(tf.float32, [None, config.num_classes], name='input_y')
    keep_prob = tf.placeholder(tf.float32, name='keep_prob')


    def lstm_cell():   # lstm核
        return tf.contrib.rnn.BasicLSTMCell(config.hidden_dim, state_is_tuple=True)

    def gru_cell():  # gru核
        return tf.contrib.rnn.GRUCell(config.hidden_dim)

    def dropout(): # 为每一个rnn核后面加一个dropout层
        if (config.rnn == 'lstm'):
            cell = lstm_cell()
        else:
            cell = gru_cell()
        return tf.contrib.rnn.DropoutWrapper(cell, output_keep_prob=keep_prob)

    # 词向量映射
    with tf.device('/cpu:0'):
        embedding = tf.get_variable('embedding', [config.vocab_size, config.embedding_dim])
        embedding_inputs = tf.nn.embedding_lookup(embedding, input_x)

    with tf.name_scope("rnn"):
        # 多层rnn网络
        cells = [dropout() for _ in range(config.num_layers)]
        rnn_cell = tf.contrib.rnn.MultiRNNCell(cells, state_is_tuple=True)

        _outputs, _ = tf.nn.dynamic_rnn(cell=rnn_cell, inputs=embedding_inputs, dtype=tf.float32)
        last = _outputs[:, -1, :]  # 取最后一个时序输出作为结果

    with tf.name_scope("score"):
        # 全连接层，后面接dropout以及relu激活
        fc = tf.layers.dense(last, config.hidden_dim, name='fc1')
        fc = tf.contrib.layers.dropout(fc, keep_prob)
        fc = tf.nn.relu(fc)

        # 分类器
        logits = tf.layers.dense(fc, config.num_classes, name='fc2')
        y_pred_cls = tf.argmax(tf.nn.softmax(logits), 1)  # 预测类别

    with tf.name_scope("optimize"):
        # 损失函数，交叉熵
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=input_y)
        loss = tf.reduce_mean(cross_entropy)
        # 优化器
        optim = tf.train.AdamOptimizer(learning_rate=config.learning_rate).minimize(loss)

    with tf.name_scope("accuracy"):
        # 准确率
        correct_pred = tf.equal(tf.argmax(input_y, 1), y_pred_cls)
        acc = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    return optim,acc