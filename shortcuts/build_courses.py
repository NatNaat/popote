#!/usr/bin/env python3
"""Génère Courses.shortcut : reçoit la liste de courses (une ligne par article) et crée un rappel par ligne
dans la liste Rappels « Courses ». Signé avec l'outil `shortcuts` de macOS.

Usage : python3 build_courses.py   → Courses.shortcut à envoyer sur l'iPhone (AirDrop / iCloud Drive), puis à ouvrir.
Popote l'appelle par : shortcuts://run-shortcut?name=Courses&input=text&text=<liste>
"""
import plistlib, subprocess, sys, uuid
from pathlib import Path

HERE = Path(__file__).parent
LISTE_RAPPELS = "Courses"   # nom de la liste dans l'app Rappels (créée à la main si elle n'existe pas)
OBJ = "￼"


def uid(): return str(uuid.uuid4()).upper()
def att(a): return {"Value": a, "WFSerializationType": "WFTextTokenAttachment"}
def text(*parts):
    s, ranges = "", {}
    for p in parts:
        if isinstance(p, str): s += p
        else: ranges["{%d, 1}" % len(s)] = p; s += OBJ
    return {"Value": {"string": s, "attachmentsByRange": ranges}, "WFSerializationType": "WFTextTokenString"}
def action(ident, **params): return {"WFWorkflowActionIdentifier": "is.workflow.actions." + ident, "WFWorkflowActionParameters": params}

INPUT = {"Type": "ExtensionInput"}
REPEAT_ITEM = {"Type": "Variable", "VariableName": "Repeat Item"}


def courses():
    g = uid()
    return [
        action("comment", WFCommentActionText="Popote → Rappels. Entrée : la liste de courses, une ligne par article. Change le nom de la liste dans l'action « Ajouter un rappel » si besoin."),
        action("gettext", WFTextActionText=text(INPUT)),
        action("text.split", WFTextSeparator="New Lines"),
        action("repeat.each", GroupingIdentifier=g, WFControlFlowMode=0),
        action("addnewreminder", WFCalendarItemTitle=text(REPEAT_ITEM), WFCalendarItemCalendar=LISTE_RAPPELS, WFAlertEnabled=False),
        action("repeat.each", GroupingIdentifier=g, WFControlFlowMode=2),
        action("notification", WFNotificationActionTitle="Popote", WFNotificationActionBody=text("Liste envoyée dans Rappels › ", LISTE_RAPPELS, "."), WFNotificationActionSound=False),
    ]


def workflow(a, glyph=59771):
    return {"WFWorkflowClientVersion": "2302.0.4", "WFWorkflowMinimumClientVersion": 900, "WFWorkflowMinimumClientVersionString": "900",
            "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4274264319, "WFWorkflowIconGlyphNumber": glyph},
            "WFWorkflowTypes": [], "WFWorkflowInputContentItemClasses": ["WFStringContentItem"],
            "WFWorkflowHasShortcutInputVariables": True, "WFWorkflowImportQuestions": [], "WFWorkflowActions": a}


if __name__ == "__main__":
    raw, signed = HERE / "Courses.unsigned.shortcut", HERE / "Courses.shortcut"
    raw.write_bytes(plistlib.dumps(workflow(courses()), fmt=plistlib.FMT_BINARY))
    r = subprocess.run(["shortcuts", "sign", "--mode", "anyone", "--input", str(raw), "--output", str(signed)], capture_output=True, text=True)
    if r.returncode or not signed.exists():
        sys.exit("Signature impossible : " + (r.stderr.strip() or "erreur inconnue") + "\nConstruction manuelle : Texte (entrée) → Séparer le texte (retours à la ligne) → Répéter avec chaque → Ajouter un rappel (Élément répété, liste Courses).")
    raw.unlink()
    print("OK →", signed)
