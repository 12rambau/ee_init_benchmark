# ee_init_benchmark

The obective of this exercise is to check the efficiency of the highvolume endpoint of GEE Python API.

So far we were connecting the GEE using the following:
```
ee.Initialize()
```

In his [tutorial](https://gorelick.medium.com/fast-er-downloads-a2abd512aa26), N. Gorelick suggest tu use the [highvolumne](https://developers.google.com/earth-engine/cloud/highvolume) endpoint when batch donwloading images as it should be faster

```
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
```

Based on this assumption the questions for us would be:

How fast is it ?
should we use it all the time ?
What I did is run the following script N times on a m4 machine. The script randomly reuse N. Gorelick batch download on N ([1; 10000]) points with or without the highvolume entrypoint.
