from flask import Flask, render_template, request
from flask import current_app as app

@app.route("/")
def home():
  return "Hello World"
