import os
import sys
import argparse
import gradio as gr

from core.seq2seq.chatglm import ChatGLMSeq2Seq
from core.seq2seq.llama import LLAMASeq2Seq
from core.seq2seq.bloom import BLoomSeq2Seq
from core.seq2seq.qwen import QwenSeq2Seq
from core.seq2seq.baichuan import BaichuanSeq2Seq
from core.seq2seq.mixtral import MixtralSeq2Seq
from core.seq2seq.phi import PhiSeq2Seq

from core.classify.llama import LLAMAClassify
from core.classify.bloom import BLoomClassify


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inference for all.')

    # system
    parser.add_argument('--debug', action="store_true", help="Debug Mode to output detail info")
    parser.add_argument('--web', action="store_true", help="Web Demo to try the inference")

    # base
    parser.add_argument('--instruction', default="Hello", type=str)
    parser.add_argument('--input', default=None, type=str)
    parser.add_argument('--data', default=None, help="The DIR of test data", type=str)
    parser.add_argument('--model_type', default="llama", choices=['llama', 'llama2', 'chatglm', 'chatglm2', 'bloom', 'qwen', "baichuan", "mixtral", "phi"])
    parser.add_argument('--task_type', default="seq2seq", choices=['seq2seq', 'classify'])
    parser.add_argument('--labels', default="[\"0\", \"1\"]",
                        help="Labels to classify, only used when task_type is classify")
    parser.add_argument('--model_path', default="LLMs/open-llama/openllama-3b", type=str)
    parser.add_argument('--adapter_weights', default="None", type=str, help="The DIR of adapter weights")

    parser.add_argument('--load_8bit', action="store_true")

    # generate
    parser.add_argument('--temperature', default="0.7", type=float, help="temperature higher, LLM is more creative")
    parser.add_argument('--top_p', default="0.9", type=float)
    parser.add_argument('--top_k', default="40", type=int)
    parser.add_argument('--max_new_tokens', default="512", type=int)

    # fromdb
    parser.add_argument('--fromdb', action="store_true")
    parser.add_argument('--db_type', default=None, type=str, help="The record is whether 'train' or 'test'.")
    parser.add_argument('--db_iteration', default=None, type=str, help="The record's set name.")
    parser.add_argument('--db_test_iteration', default=None, type=str, help="The record's test set name.")


    args, _ = parser.parse_known_args()

    if args.task_type == "seq2seq":
        if args.model_type == "chatglm" or args.model_type == "chatglm2":
            llm = ChatGLMSeq2Seq()
        elif args.model_type == "llama" or args.model_type == "llama2":
            llm = LLAMASeq2Seq()
        elif args.model_type == "bloom":
            llm = BLoomSeq2Seq()
        elif args.model_type == "qwen":
            llm = QwenSeq2Seq()
        elif args.model_type == "baichuan":
            llm = BaichuanSeq2Seq()
        elif args.model_type == "mixtral":
            llm = MixtralSeq2Seq()
        elif args.model_type == "phi":
            llm = PhiSeq2Seq()
        else:
            print("model_type should be llama/llama2/bloom/chatglm/chatglm2/qwen/baichuan/mixtral/phi")
            sys.exit(-1)
    elif args.task_type == "classify":
        if args.model_type == "chatglm" or args.model_type == "chatglm2":
            print("Classify with ChatGLM is not support now.")
            sys.exit(-1)
        elif args.model_type == "llama" or args.model_type == "llama2":
            llm = LLAMAClassify()
        elif args.model_type == "bloom":
            llm = BLoomClassify()
        elif args.model_type == "qwen":
            print("Classify with Qwen is not support now.")
            sys.exit(-1)
        elif args.model_type == "baichuan":
            print("Classify with Baichuan is not support now.")
            sys.exit(-1)
        elif args.model_type == "mixtral":
            print("Classify with Mixtral is not support now.")
            sys.exit(-1)
        elif args.model_type == "phi":
            print("Classify with Phi is not support now.")
            sys.exit(-1)
        else:
            print("model_type should be llama/llama2/bloom/chatglm/chatglm2/qwen/baichuan/mixtral/phi")
            sys.exit(-1)

    llm.debug = args.debug
    llm.web = args.web

    llm.base_model = args.model_path
    llm.adapter_weights = args.adapter_weights

    llm.load_8bit = args.load_8bit

    llm.temperature = args.temperature
    llm.top_p = args.top_p
    llm.top_k = args.top_k
    llm.max_new_tokens = args.max_new_tokens

    if args.web:
        model = llm.load_model()
        def parse_text(text):
            lines = text.split("\n")
            lines = [line for line in lines if line != ""]
            count = 0
            for i, line in enumerate(lines):
                if "```" in line:
                    count += 1
                    items = line.split('`')
                    if count % 2 == 1:
                        lines[i] = f'<pre><code class="language-{items[-1]}">'
                    else:
                        lines[i] = f'<br></code></pre>'
                else:
                    if i > 0:
                        if count % 2 == 1:
                            line = line.replace("`", "\`")
                            line = line.replace("<", "&lt;")
                            line = line.replace(">", "&gt;")
                            line = line.replace(" ", "&nbsp;")
                            line = line.replace("*", "&ast;")
                            line = line.replace("_", "&lowbar;")
                            line = line.replace("-", "&#45;")
                            line = line.replace(".", "&#46;")
                            line = line.replace("!", "&#33;")
                            line = line.replace("(", "&#40;")
                            line = line.replace(")", "&#41;")
                            line = line.replace("$", "&#36;")
                        lines[i] = "<br>" + line
            text = "".join(lines)
            return text

        def predict(input, chatbot, history):
            chatbot.append((parse_text(input), ""))
            response = llm.evaluate(model, "", input)
            # print(response)
            chatbot[-1] = (parse_text(input), response)

            yield chatbot, history

        def reset_user_input():
            return gr.update(value='')

        def reset_state():
            return [], []


        with gr.Blocks(
                title="TryLLM"
        ) as demo:
            gr.HTML("""<h1 align="center">LLM: {}</h1>""".format(args.model_type))

            with gr.Row():
                chatbot = gr.Chatbot()
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Column(scale=12):
                        user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=10).style(
                            container=False)
                    with gr.Column(min_width=32, scale=1):
                        submitBtn = gr.Button("Submit", variant="primary")
                with gr.Column(scale=1):
                    emptyBtn = gr.Button("Clear History")

            history = gr.State([])

            submitBtn.click(predict, inputs=[user_input, chatbot, history], outputs=[chatbot, history],
                            show_progress=True)
            submitBtn.click(reset_user_input, [], [user_input])

            emptyBtn.click(reset_state, inputs=[], outputs=[chatbot, history], show_progress=True)

        if os.getenv("DEBUG"):
            demo.queue().launch(share=False, inbrowser=True)
        else:
            demo.queue().launch(server_name="0.0.0.0", server_port=7861, share=False,
                                inbrowser=False)

    else:
        llm.generate(args.instruction, args.input, args.data, args.fromdb, args.db_type, args.db_iteration, args.db_test_iteration)

