import tkinter as tk

def on_click(button_text):
    if button_text == 'C':
        display.delete(0, tk.END)
    elif button_text == '=':
        try:
            # Replaces ^ with ** for Python math
            expression = display.get().replace('^', '**')
            result = eval(expression)
            display.delete(0, tk.END)
            display.insert(0, str(result))
        except Exception:
            display.delete(0, tk.END)
            display.insert(0, "Error")
    else:
        display.insert(tk.END, button_text)

root = tk.Tk()
root.title("CSC426 Calculator")

display = tk.Entry(root, width=20, font=('Arial', 24))
display.grid(row=0, column=0, columnspan=4)

buttons = ['7','8','9','/', '4','5','6','*', '1','2','3','-', '0','C','=','+', '^', '%']

# Create buttons in a 4x4 grid layout
row = 1
col = 0
for button_text in buttons:
    btn = tk.Button(root, text=button_text, font=('Arial', 18), 
                    command=lambda text=button_text: on_click(text))
    btn.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
    col += 1
    if col > 3:
        col = 0
        row += 1

# Configure grid weights for better resizing
for i in range(5):
    root.grid_rowconfigure(i, weight=1)
for i in range(4):
    root.grid_columnconfigure(i, weight=1)

root.mainloop()
