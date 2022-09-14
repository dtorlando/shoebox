# used with file manipulation
import os

# stores/retrieves objects as files, convenient so we won't have to re-make objects from csv files every time
# which is computationally expensive
import pickle

# contains all file paths we will be working with to original files and major pickled files
# the main file is acting like it exists in the backend folder, dunno why
#   need to fix that
base_path = '../corpora/'
pickled_files = {'links': base_path + 'links.p',
                 'bases': base_path + 'bases.p',
                 'sentences': base_path + 'sentences.p'}
original_files = {'links': base_path + 'links.csv',
                  'bases': base_path + 'base_sentences.csv',
                  'sentences': base_path + 'raw_sentences.csv'}

# language codes for languages we would probably want to work in, ie english, russian, japanese etc
language_codes = ['eng', 'rus', 'ita', 'tur', 'fra', 'por', 'spa', 'hun', 'jpn', 'fin', 'cmn',
                  'ell', 'vie', 'isl', 'kor', 'deu']


# clears all pickle (.p) files (for wanting re-generation)
def clear_pickles(clear_the_pickles):
    if clear_the_pickles:
        for file_name in os.listdir(base_path):
            file = os.path.join(base_path, file_name)
            try:
                if os.path.isfile(file) and file.endswith('.p'):
                    os.remove(file)
            except IndexError:
                assert True, file + ': error occurred with this file'


# base_links has ~10.7 million keys
def create_bases():
    base_links = {}
    try:
        with open(pickled_files['bases'], 'rb') as f:
            base_links = pickle.load(f)
            print("base pickle successfully loaded")
    except IOError:
        print("base pickle failed to load, being created..")
        with open(original_files['bases'], 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # csv file contains sentence which matches to a base
                # ie This is an example sentence // '0'
                # ie Here is another sentence. // '15343'
                # if the base is '0', the sentence is an original
                # if the base is a string of a number,
                #   that corresponds to the id of the sentence from where it was translated
                a, b = line.split('\t')
                assert a.strip() not in base_links, a + " \nthis sentence already in the links file"
                base_links[a.strip()] = b.strip()
        pickle.dump(base_links, open(pickled_files['bases'], 'wb'))

    assert len(base_links) > 0, 'base_links has a 0 length'
    return base_links


# links has ~9 million keys
def create_links():
    sentence_links = {}
    try:
        with open(pickled_files['links'], 'rb') as f:
            sentence_links = pickle.load(f)
            print("links pickle was successfully loaded")
    except IOError:
        print('links pickle failed to load... being created')
        with open(original_files['links'], 'r', encoding='utf-8') as f:
            for line in f.readlines():

                # this file contains sentence_id to sentence_id links which represent translations
                # one id may map to multiple translations, thus each key maps to a list of keys
                a, b = line.split('\t')
                sentence_links.setdefault(a.strip(), [])
                sentence_links[a.strip()].append(b.strip())
        pickle.dump(sentence_links, open(pickled_files['links'], 'wb'))

    assert len(sentence_links) != 0, 'sentence links has a 0 length'
    return sentence_links


# sentences is a very large map, and thus is broken up into smaller language-specific submaps
# for the 16 chosen languages, the combined key size is ~6.9 million
def create_sentences():
    sentences = {}
    try:
        with open(pickled_files['sentences'], 'rb') as f:
            sentences = pickle.load(f)
            print("sentence pickle was successfully loaded")
    except IOError:
        print("sentence pickle failed to load... being created")
        with open(original_files['sentences'], 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # each line is composed of a unique id, the language, and the actual sentence
                sentence_id, language, sentence = line.split('\t')
                # as there are >400 languages,
                #   we only want to obtain sentences from one of our chosen languages
                # a large map of language-specific maps is created,
                #   with submaps mapping ids to sentences for that language
                if language.strip() in language_codes:
                    sentences.setdefault(language.strip(), {})
                    sentences[language.strip()][sentence_id.strip()] = sentence.strip()

        # an empty sentences.p file is created as a basic check for when needing to re-create all submaps
        pickle.dump({}, open(pickled_files['sentences'], 'wb'))

        for language, language_submap in sentences.items():
            # each language-specific submap (english, russian, etc) is dumped into its own file
            pickle.dump(language_submap, open(base_path + language + '.p', 'wb'))


# returns the pickled sub-map for language specified
def get_sentences_pickle(language):
    assert language in language_codes, 'wrong language code given'

    language_d = None

    try:
        with open(base_path + language + '.p', 'rb') as f:
            language_d = pickle.load(f)
    except IOError:
        assert True, 'no such pickle exists for type ' + language

    return language_d


# isolated code for playing with programgit
def sandbox():
    spa_d = get_sentences_pickle('spa')
    eng_d = get_sentences_pickle('eng')

    english_word_count = {}
    spanish_word_count = {}

    for v in eng_d.values():
        for wordThing in v.split(' '):
            english_word_count.setdefault(wordThing.strip().lower(), 0)
            english_word_count[wordThing.strip().lower()] = english_word_count[wordThing.strip().lower()] + 1;

    for v in spa_d.values():
        for wordThing in v.split(' '):
            spanish_word_count.setdefault(wordThing.strip().lower(), 0)
            spanish_word_count[wordThing.strip().lower()] = spanish_word_count[wordThing.strip().lower()] + 1;

    listy = [(k, v) for k, v in spanish_word_count.items()]
    listy.sort(key=lambda x: x[1], reverse=True)
    for e in listy:
        if e[1] > 1000:
            print(e)

    # por_d = get_pickle('por')
    # deu_d = get_pickle('deu')
    #
    # for k, v in eng_d.items():
    #         print(k, v)
    #         if k in links:
    #             # print(links[k])
    #             for e in links[k]:
    #                 # if e in eng_d and e != k:
    #                 #     print(k, v)
    #                 #     print(eng_d[e])
    #                 # if e in spa_d:
    #                 #     print(spa_d[e])
    #                 if e in fra_d:
    #                     print(fra_d[e])
    #                 # if e in spa_d:
    #                 #     print(spa_d[e])
    #                 # if e in fra_d:
    #                 #     print(fra_d[e])
    #                 # if e in por_d:
    #                 #     print(por_d[e])
    #                 # if e in deu_d:
    #                 #     print(deu_d[e])
    #         else:
    #             print('this key is not in links')


def main():
    # set to True if you wish to delete all saved pickles (re-generation is time consuming)
    clear_pickles(False)

    bases = create_bases()
    links = create_links()
    create_sentences()

    sandbox()


# program starting point
main()
