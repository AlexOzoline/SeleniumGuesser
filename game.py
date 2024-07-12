import random
import os
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Initialize the Chrome WebDriver with headless mode
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.page_load_strategy = 'eager'
driver = webdriver.Chrome(options=chrome_options)

# File to store user statistics
STATS_FILE = "guess_game_stats.txt"

class GuessGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCEguessr")
        self.correct_guesses = 0
        self.incorrect_guesses = 0
        self.total_guesses = 0
        
        self.setup_gui()
        self.load_stats()
        self.new_game()

    def setup_gui(self):
        self.blue_team_label = tk.Label(self.root, text="Blue Team:")
        self.blue_team_label.pack()

        self.blue_team_listbox = tk.Listbox(self.root)
        self.blue_team_listbox.pack()

        self.red_team_label = tk.Label(self.root, text="Red Team:")
        self.red_team_label.pack()

        self.red_team_listbox = tk.Listbox(self.root)
        self.red_team_listbox.pack()

        self.guess_label = tk.Label(self.root, text="Who do you think won?")
        self.guess_label.pack()

        self.blue_var = tk.BooleanVar()
        self.blue_check = tk.Checkbutton(self.root, text="Blue", variable=self.blue_var)
        self.blue_check.pack()

        self.red_var = tk.BooleanVar()
        self.red_check = tk.Checkbutton(self.root, text="Red", variable=self.red_var)
        self.red_check.pack()

        self.submit_button = tk.Button(self.root, text="Submit Guess", command=self.submit_guess)
        self.submit_button.pack()

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack()

        self.score_label = tk.Label(self.root, text="Score: 0%")
        self.score_label.pack()

        self.total_guesses_label = tk.Label(self.root, text="Total Guesses: 0")
        self.total_guesses_label.pack()

    def new_game(self):
        try:
            # Fetch data for new game
            self.blue_team, self.red_team, self.winner = self.fetch_game_data()

            # Clear the listboxes
            self.blue_team_listbox.delete(0, tk.END)
            self.red_team_listbox.delete(0, tk.END)
            
            # Update the listboxes with new data
            for champ, summoner in self.blue_team:
                self.blue_team_listbox.insert(tk.END, f"{champ} ({summoner})")
            
            for champ, summoner in self.red_team:
                self.red_team_listbox.insert(tk.END, f"{champ} ({summoner})")

            self.result_label.config(text="")
            self.blue_var.set(False)
            self.red_var.set(False)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.new_game()

    def fetch_game_data(self):
        driver.get("https://www.op.gg/leaderboards/tier?region=oce")

        randint = random.randint(0, 50)
        randint2 = str(random.randint(1, 5))
        tr_elements = driver.find_elements(By.XPATH, "/html/body/div[1]/div[6]/div[3]/table/tbody/tr")
        print(tr_elements)

        txt = tr_elements[randint].text
        newline_indices = [index for index, char in enumerate(txt) if char == "\n"]
        summoner_name = txt[newline_indices[0] + 1:newline_indices[1]] + txt[newline_indices[1] + 1:newline_indices[2]]
        summoner_name_encoded = summoner_name.replace(" ", "%20")
        splitted = summoner_name_encoded.split('#')
        acc_url = "https://www.op.gg/summoners/oce/" + splitted[0] + '-' + splitted[1] + "?queue_type=SOLORANKED"
        driver.get(acc_url)

        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div[9]/div[2]/div[3]/div[{randint2}]")))

            game_xpath = f"/html/body/div[1]/div[9]/div[2]/div[3]/div[{randint2}]"
            game_result = driver.find_element(By.XPATH, game_xpath + "/div").get_attribute("class")
            result = "loss" if "LOSE" in game_result else "win"

            blue_team = []
            red_team = []
            for i in range(1, 11):
                champ_name_xpath = game_xpath + f"/div/div[2]/div/div[3]/div[{i}]/div[1]/img"
                summoner_name_element = driver.find_element(By.XPATH, game_xpath + f"/div/div[2]/div/div[3]/div[{i}]/div[2]/div/a/div/span")
                champ_element = driver.find_element(By.XPATH, champ_name_xpath)
                champ_alt = champ_element.get_attribute("alt")
                if i < 6:
                    blue_team.append((champ_alt, summoner_name_element.text))
                else:
                    red_team.append((champ_alt, summoner_name_element.text))

            for champ, name in blue_team:
                if name == summoner_name.split('#')[0]:
                    winner = "blue" if result == "win" else "red"

            for champ, name in red_team:
                if name == summoner_name.split('#')[0]:
                    winner = "red" if result == "win" else "blue"

            return blue_team, red_team, winner
        except TimeoutException:
            raise TimeoutException("Loading game data took too long.")
        except NoSuchElementException:
            raise NoSuchElementException("Could not find game data on the page.")

    def submit_guess(self):
        if self.blue_var.get():
            guess = "blue"
        elif self.red_var.get():
            guess = "red"
        else:
            messagebox.showerror("Error", "Please select a team.")
            return
        if guess == self.winner:
            self.correct_guesses += 1
            correct = True
        else:
            self.incorrect_guesses += 1
            correct = False

        self.total_guesses += 1
        self.update_score()
        self.save_stats()
        self.new_game()
        if correct:
            self.result_label.config(text="You guessed correctly!!", fg="green")
        else:
            self.result_label.config(text="You were wrong!", fg="red")

    def update_score(self):
        total_guesses = self.correct_guesses + self.incorrect_guesses
        if total_guesses > 0:
            success_rate = (self.correct_guesses / total_guesses) * 100
        else:
            success_rate = 0
        self.score_label.config(text=f"Score: {success_rate:.2f}%")
        self.total_guesses_label.config(text=f"Total Guesses: {self.total_guesses}")

    def load_stats(self):
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats = f.read().split(',')
                if len(stats) == 3:
                    self.correct_guesses = int(stats[0])
                    self.incorrect_guesses = int(stats[1])
                    self.total_guesses = int(stats[2])
        self.update_score()

    def save_stats(self):
        with open(STATS_FILE, 'w') as f:
            f.write(f"{self.correct_guesses},{self.incorrect_guesses},{self.total_guesses}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GuessGameApp(root)
    root.mainloop()

    # Close the driver when the app closes
    driver.quit()
