"""Defines the neural network, losss function and metrics"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):

    def __init__(self, params):
        super(Net, self).__init__()

        # the embedding takes as input the vocab_size and the embedding_dim
        weight = torch.tensor(np.load(params.embedding_path), dtype=torch.float)
        self.embedding = nn.Embedding.from_pretrained(weight)
        self.pos_embedding = nn.Embedding(params.number_of_pos, params.pos_embd_dim)

        # the LSTM takes as input the size of its input (embedding_dim), its hidden size
        # for more details on how to use it, check out the documentation
        self.lstm = nn.LSTM(params.embedding_dim + params.pos_embd_dim, params.lstm_hidden_dim, bidirectional=True,
                            batch_first=True)

        # the fully connected layer transforms the output to give the final output layer
        self.fc1 = nn.Linear(params.lstm_hidden_dim * 2, params.fc1)
        self.fc2 = nn.Linear(params.fc1, params.number_of_tags)

    def forward(self, s, pos):
        """
        This function defines how we use the components of our network to operate on an input batch.

        Args:
            s: (Variable) contains a batch of sentences, of dimension batch_size x seq_len, where seq_len is
               the length of the longest sentence in the batch. For sentences shorter than seq_len, the remaining
               tokens are PADding tokens. Each row is a sentence with each element corresponding to the index of
               the token in the vocab.

        Returns:
            out: (Variable) dimension batch_size*seq_len x num_tags with the log probabilities of tokens for each token
                 of each sentence.

        Note: the dimensions after each step are provided
        """
        #                                -> batch_size x seq_len
        # apply the embedding layer that maps each token to its embedding
        s = self.embedding(s)  # dim: batch_size x seq_len x embedding_dim
        p = self.pos_embedding(pos)

        s = torch.cat((s, p), dim=2)

        # run the LSTM along the sentences of length seq_len
        s, _ = self.lstm(s)  # dim: batch_size x seq_len x lstm_hidden_dim

        # make the Variable contiguous in memory (a PyTorch artefact)
        s = s.contiguous()

        # reshape the Variable so that each row contains one token
        s = s.view(-1, s.shape[2])  # dim: batch_size*seq_len x lstm_hidden_dim

        # apply the fully connected layer and obtain the output (before softmax) for each token
        s = self.fc1(s)  # dim: batch_size*seq_len x num_tags
        s = self.fc2(s)  # dim: batch_size*seq_len x num_tags

        # apply log softmax on each token's output (this is recommended over applying softmax
        # since it is numerically more stable)
        return F.log_softmax(s, dim=1)  # dim: batch_size*seq_len x num_tags
