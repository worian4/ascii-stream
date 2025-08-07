#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <vector>
#include <string>
#include <iostream>
#include <cstdio>

//python setup.py build_ext --inplace     <- to add library

static std::vector<std::string> prev_lines;

static PyObject* render_frame(PyObject* self, PyObject* args) {
    const char* frame_cstr;
    if (!PyArg_ParseTuple(args, "s", &frame_cstr))
        return NULL;

    std::string frame(frame_cstr);
    std::vector<std::string> lines;
    size_t pos = 0, prev = 0;
    while ((pos = frame.find('\n', prev)) != std::string::npos) {
        lines.push_back(frame.substr(prev, pos - prev));
        prev = pos + 1;
    }
    lines.push_back(frame.substr(prev));

    std::cout << "\x1b[H";

    size_t updated_lines = 0;
    for (size_t i = 0; i < lines.size(); ++i) {
        bool different = (i >= prev_lines.size() || lines[i] != prev_lines[i]);
        if (different) {
            std::cout << "\x1b[" << (i + 1) << ";1H" << lines[i];
            ++updated_lines;
        }
    }
    std::cout.flush();
    prev_lines = lines;

    return PyLong_FromSize_t(updated_lines);
}

static PyMethodDef RenderFuncsMethods[] = {
    {"render_frame", render_frame, METH_VARARGS, "Render ASCII frame with partial updates"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef renderfuncsmodule = {
    PyModuleDef_HEAD_INIT,
    "render_funcs", /* name of module */
    NULL,          /* module documentation, may be NULL */
    -1,
    RenderFuncsMethods
};

PyMODINIT_FUNC PyInit_render_funcs(void) {
    return PyModule_Create(&renderfuncsmodule);
}
