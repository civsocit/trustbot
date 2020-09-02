from enum import Enum, auto
from typing import Optional, Dict, List, Tuple, Set, Iterable
from dataclasses import dataclass
from itertools import chain
from os.path import isfile
import pickle


class Relation(Enum):
    bad = auto()
    neutral = auto()
    good = auto()


@dataclass()
class Comment:
    relation: Relation
    user_from: str
    user_to: str
    comment: Optional[str]

    def __hash__(self):
        return hash(self.user_to + self.user_from)

    @property
    def relation_s(self):
        return {
            Relation.bad: "не доверяю",
            Relation.neutral: "нейтрально",
            Relation.good: "доверяю"
        }[self.relation]


class Database:

    _backup_path = "backup.dat"

    def __init__(self):
        self._data: Dict[str, List[Comment]] = dict()

    @classmethod
    def restore_backup(cls) -> "Database":
        if isfile(cls._backup_path):
            with open(cls._backup_path, "rb") as file:
                return pickle.load(file)
        return Database()

    def save_backup(self):
        with open(self._backup_path, "wb") as file:
            pickle.dump(self, file)

    def add_relation(self, user_from: str, user_to: str, relation: Relation, comment_str: Optional[str]):
        comment = Comment(relation=relation, user_from=user_from, user_to=user_to, comment=comment_str)

        if comment.user_from == comment.user_to:
            raise ValueError("Self-comments are prohibited!")

        # Here are no comments from user_from user
        if user_from not in self._data:
            self._data[user_from] = [comment]
            return

        for index, exist_comment in enumerate(self._data[user_from]):
            # Comment from user_from to user_to already exists
            if exist_comment.user_to == user_to:
                self._data[user_from].pop(index)   # So, remove that comment
                break
        # Here are no comment from user_from to user_to
        self._data[user_from].append(comment)

    def _get_trusted_users_one_depth(self, user_from: str) -> Set[str]:
        return {comment.user_to for comment in self._data.get(user_from, []) if comment.relation is Relation.good}

    def get_trusted_users(self, user_from: str) -> Tuple[Set[str], Set[str], Set[str]]:

        # TODO: parametrize depth level
        # TODO: optimization!

        first_level = self._get_trusted_users_one_depth(user_from)

        second_level = set(
            chain(*[self._get_trusted_users_one_depth(user) for user in first_level])
        )

        # Recursion protection
        second_level -= first_level

        third_level = set(
            chain(*[self._get_trusted_users_one_depth(user) for user in second_level])
        )

        # Recursion protection
        third_level -= first_level
        third_level -= second_level

        return first_level, second_level, third_level

    def get_comments(self, users_from: Iterable[str], user_to: str) -> Set[Comment]:
        comments = []

        for user in users_from:
            for comment in self._data.get(user, []):
                if comment.user_to == user_to:
                    comments.append(comment)
                    break

        return set(comments)

    def get_trusted_comments(self, user_from: str, user_to: str) -> List[Comment]:

        # TODO: optimization!

        first_level, second_level, third_level = self.get_trusted_users(user_from)

        zero_level_comments = self.get_comments({user_from}, user_to)
        first_level_comments = self.get_comments(first_level, user_to)
        second_level_comments = self.get_comments(second_level, user_to)
        third_level_comments = self.get_comments(third_level, user_to)

        comments = list(chain(
            zero_level_comments,
            [comment for comment in first_level_comments if comment.relation is Relation.bad],
            [comment for comment in second_level_comments if comment.relation is Relation.bad],
            [comment for comment in third_level_comments if comment.relation is Relation.bad],
            [comment for comment in first_level_comments if comment.relation is not Relation.bad],
            [comment for comment in second_level_comments if comment.relation is not Relation.bad],
            [comment for comment in third_level_comments if comment.relation is not Relation.bad]
        ))

        return comments


if __name__ == '__main__':
    # Some tests
    db = Database()
    db.add_relation("A", "B", Relation.good, "Cool guy!")
    db.add_relation("A", "F", Relation.good, "Nice")

    db.add_relation("B", "C", Relation.good, "So cool guy!")
    db.add_relation("F", "C", Relation.bad, "Bad gay!")

    db.add_relation("A", "C", Relation.good, "Cool guy")

    db.save_backup()
    db = Database.restore_backup()

    for comment in db.get_trusted_comments("A", "C"):
        print(comment)
