import pathlib
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List

import gspread
import pandas as pd
from dotenv import dotenv_values
from oauth2client.service_account import ServiceAccountCredentials

config = dotenv_values("../.env")


PRIVATE_KEY = pathlib.Path.cwd() / config["PRIVATE_KEY_FILE"]
GOOGLE_SHEET_FEEDS = "https://spreadsheets.google.com/feeds"
DATE_MMDDYY = "%m-%d-%y"


def _connect_to_google_sheets(privatekey: str):
    scope = [GOOGLE_SHEET_FEEDS]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(privatekey, scope)
    gc = gspread.authorize(credentials)
    return gc


def _get_book(gc, spreadsheet_key: str):
    return gc.open_by_key(spreadsheet_key)


def _worksheet_to_df(worksheet_name, book):
    worksheet = book.worksheet(worksheet_name)
    table = worksheet.get_all_values()
    return pd.DataFrame(table[1:], columns=table[0])


def read_worksheet(worksheet_name, spreadsheet_key):
    gc = _connect_to_google_sheets(PRIVATE_KEY)
    book = _get_book(gc, spreadsheet_key)
    return _worksheet_to_df(worksheet_name, book)


def get_formatted_date(hw_name: str, df_schedule):
    duedate = df_schedule[df_schedule.Topic.str.contains(hw_name)].Date
    return date.fromisoformat(duedate.values[0]).strftime(DATE_MMDDYY)


def format_homework_problems(df_hw: pd.DataFrame, df_textbook: pd.DataFrame) -> List[str]:
    """
    Formats the dataframes into a pretty string.

    :param pd.DataFrame df_hw: Columns [Chapter, Section, Problem]
    :param pd.DataFrame df_textbook: Columns [Chapter, Section, Description]
    :return List[str] document_strings:
    """
    document_strings = []
    for each in df_hw.merge(
        df_textbook, how="inner", on=["Chapter", "Section"]
    ).groupby(["Chapter", "Section"]):
        chapter = each[0][0]
        section = each[0][1]
        topic = df_textbook[
            (df_textbook.Chapter == chapter) & (df_textbook.Section == section)
        ].Description.values[0]
        problems = list_to_string([int(x) for x in each[1].Problem.values])
        document_strings.append(f"{chapter}.{section} {topic}: {problems}")
    return document_strings


def list_to_string(my_list):
    return str(my_list)[1:-1]


@dataclass
class Section:
    chapter: int
    section: int
    topic: str

    def __repr__(self):
        return f"{self.chapter}.{self.section} {self.topic}"


class SectionProblems:
    def __init__(self, section: Section, problems):
        self.section = section
        self.problems = problems

    def __repr__(self):
        return f"{self.section}: {list_to_string(self.problems)}"


class DifficultyLevel(Enum):
    easy = 1
    medium = 2
    hard = 3


@dataclass
class Problem:
    chapter: int
    section: int
    number: int
    solution: str
    difficulty: DifficultyLevel
    comments: str
