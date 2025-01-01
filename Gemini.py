import grpc
import re
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog, messagebox, font
import webbrowser
import asyncio
from concurrent.futures import ThreadPoolExecutor

def start_app():
    root = tk.Tk()
    root.title("Sınav Soruları Değerlendirme Platformu")
    root.geometry("900x700")
    root.configure(bg="#f7f7f7")

    title_font = font.Font(family="Arial", size=26, weight="bold")
    button_font = font.Font(family="Arial", size=14, weight="bold")
    label_font = font.Font(family="Arial", size=12)

    header_frame = tk.Frame(root, bg="#4a4e69")
    header_frame.pack(fill=tk.X)

    title_label = tk.Label(header_frame, text="Sınav Soruları Değerlendirme Platformu", bg="#4a4e69", fg="white", font=title_font, pady=15)
    title_label.pack()

    main_frame = tk.Frame(root, bg="#f7f7f7", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    loading_label = tk.Label(main_frame, text="", bg="#f7f7f7", font=label_font)
    loading_label.pack(pady=10)

    response_frame = tk.Frame(main_frame, bg="#ffffff", bd=2, relief=tk.GROOVE, padx=10, pady=10)
    response_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    video_frame = tk.Frame(main_frame, bg="#f7f7f7")
    video_frame.pack(pady=10, fill=tk.X)

    link_button = tk.Button(video_frame, text="Bilgilendirici Video İzle", command=lambda: open_video_link(current_video_link), bg="#6c757d", fg="white", font=button_font)
    link_button.pack(side=tk.RIGHT, padx=10)
    link_button.config(state=tk.DISABLED)

    navigation_frame = tk.Frame(main_frame, bg="#f7f7f7")
    navigation_frame.pack(fill=tk.X, pady=10)

    prev_button = tk.Button(navigation_frame, text="Önceki Soru", command=lambda: show_response(-1), bg="#007bff", fg="white", font=button_font, width=15)
    prev_button.pack(side=tk.LEFT, padx=5)

    next_button = tk.Button(navigation_frame, text="Sonraki Soru", command=lambda: show_response(1), bg="#007bff", fg="white", font=button_font, width=15)
    next_button.pack(side=tk.RIGHT, padx=5)

    current_video_link = None
    question_index = 0
    responses = []

    def open_video_link(video_link):
        if video_link:
            webbrowser.open(video_link)

    def show_loading(message):
        loading_label.config(text=message)
        loading_label.update_idletasks()
        loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def hide_loading():
        loading_label.config(text="")
        loading_label.place_forget()

    def reset_app():
        nonlocal question_index, responses, current_video_link
        question_index = 0
        responses = []
        current_video_link = None
        for widget in response_frame.winfo_children():
            widget.destroy()
        link_button.config(state=tk.DISABLED)

    async def evaluate_question(question, chat):
        try:
            response = await chat.send_message_async(question)

            yuzde_match = re.search(r'(%\d{1,3})', response.text)
            dogruluk_yuzdesi = yuzde_match.group(0).strip('%') if yuzde_match else "Belirtilmedi"
            en_dogru_cevap = response.text.split('En Doğru Cevap: ')[-1].split("Kaynak Linki:")[0].strip()
            video_link_match = re.search(r'Kaynak Linki: (https?://[^\s]+)', response.text)
            video_link = video_link_match.group(1) if video_link_match else ""

            formatted_response = f"Soru: {question}\nDoğruluk Yüzdesi: %{dogruluk_yuzdesi}\nEn Doğru Cevap: {en_dogru_cevap}"
            if video_link:
                formatted_response += f"\nKaynak Linki: {video_link}"

            return (formatted_response, video_link)
        except Exception as e:
            return (f"Soru: {question}\nYanıt: Format uygun değil - Hata: {str(e)}", None)

    async def evaluate_questions():
        nonlocal question_index
        show_loading("Cevaplanmayı Bekliyor...")
        education_level = var.get()
        if not education_level:
            hide_loading()
            messagebox.showerror("Hata", "Lütfen bir eğitim seviyesi seçin!")
            return

        genai.configure(api_key="AIzaSyDN9BEaJ2hAsbw4Gix9wY4dEANNb_obdnI")
        model = genai.GenerativeModel("gemini-1.5-flash")

        chat_history = [
            {"role": "user", "parts": (
                "Aşağıdaki sorular, farklı eğitim seviyesindeki öğrencilerin sınav sorularıdır. "
                "Cevapları değerlendirirken, seçilen eğitim seviyesine uygun olup olmadığını belirle. "
                "Cevabın doğruluk yüzdesini ve en doğru cevabı belirt. "
                "Eğer doğruluk yüzdesi %70'in altında ise güvenilir bir kaynak öner. "
                "Yanıt formatı: 'Doğruluk Yüzdesi: %X\nEn Doğru Cevap: [Doğru cevap buraya]\nKaynak Linki: [URL]'"
            )}
        ]
        chat = model.start_chat(history=chat_history)

        questions_file_path = filedialog.askopenfilename(title="Sorular dosyasını seçin", filetypes=[("Text files", "*.txt")])
        if not questions_file_path:
            hide_loading()
            return

        reset_app()

        output_file_path = "cevaplar.txt"
        output_file_path = filedialog.asksaveasfilename(initialfile=output_file_path, defaultextension=".txt", title="Cevaplar dosyasını kaydedin", filetypes=[("Text files", "*.txt")])
        if not output_file_path:
            hide_loading()
            return

        with open(questions_file_path, "r", encoding="utf-8") as file:
            questions = [line.strip() for line in file.readlines()]

        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [asyncio.ensure_future(evaluate_question(question, chat)) for question in questions]
            results = await asyncio.gather(*tasks)

        responses.extend(results)

        with open(output_file_path, "w", encoding="utf-8") as output_file:
            for resp, link in responses:
                output_file.write(resp + "\n")

        messagebox.showinfo("Tamamlandı", f"Cevaplar başarıyla kaydedildi: {output_file_path}")
        hide_loading()
        show_response(0)

    def start_evaluation_thread():
        asyncio.run(evaluate_questions())

    def show_response(direction):
        nonlocal question_index, current_video_link
        if 0 <= question_index + direction < len(responses):
            question_index += direction
            response, link = responses[question_index]
            response_frame.config(bg="#ffffff")
            for widget in response_frame.winfo_children():
                widget.destroy()

            question_label = tk.Label(response_frame, text=response.split('\n')[0], bg="#ffffff", font=label_font, justify=tk.LEFT)
            question_label.pack(pady=5)

            percentage_label = tk.Label(response_frame, text=response.split('\n')[1], bg="#ffffff", font=label_font, justify=tk.LEFT)
            percentage_label.pack(pady=5)

            answer_label = tk.Label(response_frame, text=response.split('\n')[2], bg="#ffffff", font=label_font, justify=tk.LEFT)
            answer_label.pack(pady=5)

            if len(response.split('\n')) > 3 and link:
                current_video_link = link
                link_button.config(state=tk.NORMAL)
            else:
                current_video_link = None
                link_button.config(state=tk.DISABLED)

    # Eğitim seviyesi seçimi
    var = tk.StringVar(value="1")  # Varsayılan olarak ilkokul seçili
    education_frame = tk.Frame(main_frame, bg="#f7f7f7")
    education_frame.pack(pady=10)

    tk.Label(education_frame, text="Eğitim Seviyesi Seçin:", bg="#f7f7f7", font=label_font).pack(side=tk.LEFT)

    tk.Radiobutton(education_frame, text="İlköğretim", variable=var, value="1", bg="#f7f7f7", font=label_font).pack(side=tk.LEFT)
    tk.Radiobutton(education_frame, text="Ortaöğretim", variable=var, value="2", bg="#f7f7f7", font=label_font).pack(side=tk.LEFT)
    tk.Radiobutton(education_frame, text="Akademik", variable=var, value="3", bg="#f7f7f7", font=label_font).pack(side=tk.LEFT)

    start_button = tk.Button(main_frame, text="Değerlendirmeyi Başlat", command=start_evaluation_thread, bg="#28a745", fg="white", font=button_font)
    start_button.pack(pady=20)

    main_frame.mainloop()

start_app()
